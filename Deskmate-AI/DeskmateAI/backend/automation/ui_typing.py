# DeskmateAI/backend/automation/ui_typing.py

import os
import sys
import time

# ============================================================
# UI TYPING FOR DESKMATEAI
# Handles all text input and keyboard operations
# Dictation, typing, shortcuts, clipboard operations
# Uses pyperclip + ctrl+v for all languages
# Works everywhere including Hindi/Marathi text
# Three tier: pyperclip → pyautogui → pywinauto
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Type Text ─────────────────────────────────────────────────

def type_text(text):
    """
    Type text into active window
    Uses clipboard paste for all language support
    Works for English, Hindi, Marathi and all Unicode
    Three tier: pyperclip → pyautogui write → pywinauto
    """
    # print(f"[TYPING] Typing text: {text[:50]}...")
    log_info(f"Typing text: {text[:50]}...")

    if not text:
        log_warning("Empty text to type")
        return False

    # Layer 1: pyperclip + paste (best for all languages)
    success = _type_via_clipboard(text)
    if success:
        # print(f"[TYPING] ✅ Layer 1 typing success")
        return True

    # Layer 2: pyautogui write (English only)
    success = _type_via_pyautogui(text)
    if success:
        # print(f"[TYPING] ✅ Layer 2 typing success")
        return True

    # Layer 3: pywinauto type keys
    success = _type_via_pywinauto(text)
    if success:
        # print(f"[TYPING] ✅ Layer 3 typing success")
        return True

    # print(f"[TYPING] ❌ All typing layers failed")
    log_error("All typing layers failed")
    return False


def _type_via_clipboard(text):
    """
    Layer 1: Copy to clipboard and paste
    Best method - works for ALL languages
    """
    # print(f"[TYPING] Layer 1 - clipboard paste")
    try:
        import pyperclip
        import pyautogui

        # Save current clipboard
        try:
            original_clipboard = pyperclip.paste()
        except:
            original_clipboard = ""

        # Copy text to clipboard
        pyperclip.copy(text)
        time.sleep(0.1)

        # Paste
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)

        # Restore original clipboard after small delay
        def restore_clipboard():
            time.sleep(1.0)
            try:
                pyperclip.copy(original_clipboard)
            except:
                pass

        import threading
        threading.Thread(target=restore_clipboard, daemon=True).start()

        # print(f"[TYPING] ✅ Clipboard paste done")
        log_debug("Text typed via clipboard")
        return True

    except Exception as e:
        # print(f"[TYPING] Layer 1 failed: {e}")
        log_warning(f"Clipboard paste failed: {e}")
        return False


def _type_via_pyautogui(text):
    """
    Layer 2: pyautogui write
    Works for ASCII/English only
    """
    # print(f"[TYPING] Layer 2 - pyautogui write")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False

        # Only use for ASCII text
        if all(ord(c) < 128 for c in text):
            pyautogui.write(text, interval=0.02)
            # print(f"[TYPING] ✅ pyautogui write done")
            log_debug("Text typed via pyautogui")
            return True
        else:
            # print(f"[TYPING] Layer 2 - non-ASCII text, skipping")
            return False

    except Exception as e:
        # print(f"[TYPING] Layer 2 failed: {e}")
        log_warning(f"pyautogui write failed: {e}")
        return False


def _type_via_pywinauto(text):
    """
    Layer 3: pywinauto type_keys
    """
    # print(f"[TYPING] Layer 3 - pywinauto type_keys")
    try:
        from pywinauto import Desktop
        import win32gui

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)

        if not title:
            return False

        desktop = Desktop(backend="uia")
        windows = desktop.windows()

        for window in windows:
            if title.lower() in window.window_text().lower():
                window.type_keys(text, with_spaces=True)
                # print(f"[TYPING] ✅ pywinauto type done")
                log_debug("Text typed via pywinauto")
                return True

        return False

    except Exception as e:
        # print(f"[TYPING] Layer 3 failed: {e}")
        log_error(f"pywinauto type failed: {e}")
        return False


# ── Dictation ─────────────────────────────────────────────────

def start_dictation():
    """
    Start dictation mode
    Returns True to signal pipeline to enter dictation
    Actual dictation handled by pipeline + command_handler
    """
    # print("[TYPING] Starting dictation mode...")
    log_info("Dictation mode requested")
    # Signal pipeline to enter dictation mode
    # Handled by context manager + pipeline
    return True


def type_dictated_text(text):
    """
    Type dictated text with punctuation processing
    Called by command_handler after dictation
    """
    # print(f"[TYPING] Typing dictated text: {text[:50]}...")
    log_info(f"Typing dictated: {text[:50]}...")

    from backend.utils.utils import process_punctuation
    processed = process_punctuation(text)
    # print(f"[TYPING] Processed text: {processed[:50]}...")
    return type_text(processed)


# ── Keyboard Shortcuts ────────────────────────────────────────

def copy_text():
    """Copy selected text"""
    # print("[TYPING] Copying text...")
    log_info("Copying text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'c')
        time.sleep(0.2)
        # print("[TYPING] ✅ Text copied")
        log_debug("Text copied")
        return True
    except Exception as e:
        # print(f"[TYPING] Copy failed: {e}")
        log_error(f"Copy failed: {e}")
        return False


def paste_text():
    """Paste text from clipboard"""
    # print("[TYPING] Pasting text...")
    log_info("Pasting text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'v')
        time.sleep(0.2)
        # print("[TYPING] ✅ Text pasted")
        log_debug("Text pasted")
        return True
    except Exception as e:
        # print(f"[TYPING] Paste failed: {e}")
        log_error(f"Paste failed: {e}")
        return False


def cut_text():
    """Cut selected text"""
    # print("[TYPING] Cutting text...")
    log_info("Cutting text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'x')
        time.sleep(0.2)
        # print("[TYPING] ✅ Text cut")
        log_debug("Text cut")
        return True
    except Exception as e:
        # print(f"[TYPING] Cut failed: {e}")
        log_error(f"Cut failed: {e}")
        return False


def select_all():
    """Select all text"""
    # print("[TYPING] Selecting all...")
    log_info("Selecting all text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'a')
        time.sleep(0.2)
        # print("[TYPING] ✅ All selected")
        log_debug("All text selected")
        return True
    except Exception as e:
        # print(f"[TYPING] Select all failed: {e}")
        log_error(f"Select all failed: {e}")
        return False


def undo_typing():
    """Undo last typing action"""
    # print("[TYPING] Undoing...")
    log_info("Undo typing")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'z')
        time.sleep(0.1)
        # print("[TYPING] ✅ Undone")
        log_debug("Typing undone")
        return True
    except Exception as e:
        # print(f"[TYPING] Undo failed: {e}")
        log_error(f"Undo typing failed: {e}")
        return False


def redo_typing():
    """Redo last undone typing"""
    # print("[TYPING] Redoing...")
    log_info("Redo typing")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'y')
        time.sleep(0.1)
        # print("[TYPING] ✅ Redone")
        log_debug("Typing redone")
        return True
    except Exception as e:
        # print(f"[TYPING] Redo failed: {e}")
        log_error(f"Redo typing failed: {e}")
        return False


def save_file():
    """Save current file"""
    # print("[TYPING] Saving file...")
    log_info("Saving file")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 's')
        time.sleep(0.3)
        # print("[TYPING] ✅ File saved")
        log_debug("File saved")
        return True
    except Exception as e:
        # print(f"[TYPING] Save failed: {e}")
        log_error(f"Save file failed: {e}")
        return False


def save_file_as():
    """Save file as new name"""
    # print("[TYPING] Save file as...")
    log_info("Save file as")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'shift', 's')
        time.sleep(0.3)
        # print("[TYPING] ✅ Save as dialog opened")
        log_debug("Save as dialog opened")
        return True
    except Exception as e:
        # print(f"[TYPING] Save as failed: {e}")
        log_error(f"Save as failed: {e}")
        return False


def open_file():
    """Open file dialog"""
    # print("[TYPING] Opening file...")
    log_info("Open file dialog")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'o')
        time.sleep(0.3)
        # print("[TYPING] ✅ Open dialog launched")
        log_debug("Open dialog launched")
        return True
    except Exception as e:
        # print(f"[TYPING] Open file failed: {e}")
        log_error(f"Open file failed: {e}")
        return False


def new_file():
    """Create new file"""
    # print("[TYPING] New file...")
    log_info("New file")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'n')
        time.sleep(0.3)
        # print("[TYPING] ✅ New file created")
        log_debug("New file created")
        return True
    except Exception as e:
        # print(f"[TYPING] New file failed: {e}")
        log_error(f"New file failed: {e}")
        return False


def print_file():
    """Print current file"""
    # print("[TYPING] Printing...")
    log_info("Print file")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'p')
        time.sleep(0.3)
        # print("[TYPING] ✅ Print dialog opened")
        log_debug("Print dialog opened")
        return True
    except Exception as e:
        # print(f"[TYPING] Print failed: {e}")
        log_error(f"Print failed: {e}")
        return False


def find_text():
    """Open find dialog"""
    # print("[TYPING] Find text...")
    log_info("Find text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        # print("[TYPING] ✅ Find dialog opened")
        log_debug("Find dialog opened")
        return True
    except Exception as e:
        # print(f"[TYPING] Find failed: {e}")
        log_error(f"Find failed: {e}")
        return False


def find_replace():
    """Open find and replace dialog"""
    # print("[TYPING] Find and replace...")
    log_info("Find and replace")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'h')
        time.sleep(0.3)
        # print("[TYPING] ✅ Find/replace dialog opened")
        log_debug("Find/replace dialog opened")
        return True
    except Exception as e:
        # print(f"[TYPING] Find/replace failed: {e}")
        log_error(f"Find/replace failed: {e}")
        return False


# ── Text Formatting ───────────────────────────────────────────

def bold_text():
    """Bold selected text"""
    # print("[TYPING] Bold text...")
    log_info("Bold text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'b')
        # print("[TYPING] ✅ Text bolded")
        return True
    except Exception as e:
        # print(f"[TYPING] Bold failed: {e}")
        log_error(f"Bold failed: {e}")
        return False


def italic_text():
    """Italic selected text"""
    # print("[TYPING] Italic text...")
    log_info("Italic text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'i')
        # print("[TYPING] ✅ Text italicized")
        return True
    except Exception as e:
        # print(f"[TYPING] Italic failed: {e}")
        log_error(f"Italic failed: {e}")
        return False


def underline_text():
    """Underline selected text"""
    # print("[TYPING] Underline text...")
    log_info("Underline text")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'u')
        # print("[TYPING] ✅ Text underlined")
        return True
    except Exception as e:
        # print(f"[TYPING] Underline failed: {e}")
        log_error(f"Underline failed: {e}")
        return False


# ── Navigation Keys ───────────────────────────────────────────

def press_enter():
    """Press Enter key"""
    # print("[TYPING] Pressing Enter...")
    log_info("Press Enter")
    try:
        import pyautogui
        pyautogui.press('enter')
        # print("[TYPING] ✅ Enter pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Enter failed: {e}")
        log_error(f"Press Enter failed: {e}")
        return False


def press_escape():
    """Press Escape key"""
    # print("[TYPING] Pressing Escape...")
    log_info("Press Escape")
    try:
        import pyautogui
        pyautogui.press('escape')
        # print("[TYPING] ✅ Escape pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Escape failed: {e}")
        log_error(f"Press Escape failed: {e}")
        return False


def press_tab():
    """Press Tab key"""
    # print("[TYPING] Pressing Tab...")
    log_info("Press Tab")
    try:
        import pyautogui
        pyautogui.press('tab')
        # print("[TYPING] ✅ Tab pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Tab failed: {e}")
        log_error(f"Press Tab failed: {e}")
        return False


def press_backspace():
    """Press Backspace key"""
    # print("[TYPING] Pressing Backspace...")
    log_info("Press Backspace")
    try:
        import pyautogui
        pyautogui.press('backspace')
        # print("[TYPING] ✅ Backspace pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Backspace failed: {e}")
        log_error(f"Press Backspace failed: {e}")
        return False


def press_delete():
    """Press Delete key"""
    # print("[TYPING] Pressing Delete...")
    log_info("Press Delete")
    try:
        import pyautogui
        pyautogui.press('delete')
        # print("[TYPING] ✅ Delete pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Delete failed: {e}")
        log_error(f"Press Delete failed: {e}")
        return False


def press_home():
    """Go to beginning of line"""
    # print("[TYPING] Pressing Home...")
    log_info("Press Home")
    try:
        import pyautogui
        pyautogui.press('home')
        # print("[TYPING] ✅ Home pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Home failed: {e}")
        log_error(f"Press Home failed: {e}")
        return False


def press_end():
    """Go to end of line"""
    # print("[TYPING] Pressing End...")
    log_info("Press End")
    try:
        import pyautogui
        pyautogui.press('end')
        # print("[TYPING] ✅ End pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] End failed: {e}")
        log_error(f"Press End failed: {e}")
        return False


def press_page_up():
    """Page up"""
    # print("[TYPING] Page Up...")
    log_info("Page Up")
    try:
        import pyautogui
        pyautogui.press('pageup')
        # print("[TYPING] ✅ Page Up pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Page Up failed: {e}")
        log_error(f"Page Up failed: {e}")
        return False


def press_page_down():
    """Page down"""
    # print("[TYPING] Page Down...")
    log_info("Page Down")
    try:
        import pyautogui
        pyautogui.press('pagedown')
        # print("[TYPING] ✅ Page Down pressed")
        return True
    except Exception as e:
        # print(f"[TYPING] Page Down failed: {e}")
        log_error(f"Page Down failed: {e}")
        return False


# ── Window Switching ──────────────────────────────────────────

def alt_tab():
    """Switch window with Alt+Tab"""
    # print("[TYPING] Alt+Tab...")
    log_info("Alt Tab")
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'tab')
        time.sleep(0.3)
        # print("[TYPING] ✅ Alt+Tab done")
        return True
    except Exception as e:
        # print(f"[TYPING] Alt+Tab failed: {e}")
        log_error(f"Alt Tab failed: {e}")
        return False


def press_hotkey(*keys):
    """Press any keyboard shortcut"""
    # print(f"[TYPING] Hotkey: {keys}")
    log_info(f"Hotkey: {keys}")
    try:
        import pyautogui
        pyautogui.hotkey(*keys)
        time.sleep(0.1)
        # print(f"[TYPING] ✅ Hotkey pressed: {keys}")
        log_debug(f"Hotkey pressed: {keys}")
        return True
    except Exception as e:
        # print(f"[TYPING] Hotkey failed: {e}")
        log_error(f"Hotkey failed: {e}")
        return False


# ── Special Characters ────────────────────────────────────────

def insert_special_char(char):
    """Insert special character"""
    # print(f"[TYPING] Inserting special char: {char}")
    log_info(f"Insert special char: {char}")
    try:
        import pyperclip
        import pyautogui
        pyperclip.copy(char)
        pyautogui.hotkey('ctrl', 'v')
        # print(f"[TYPING] ✅ Special char inserted: {char}")
        return True
    except Exception as e:
        # print(f"[TYPING] Special char failed: {e}")
        log_error(f"Insert special char failed: {e}")
        return False