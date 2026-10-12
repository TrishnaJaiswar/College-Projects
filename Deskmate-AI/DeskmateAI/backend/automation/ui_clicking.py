# DeskmateAI/backend/automation/ui_clicking.py

import os
import sys
import time
import numpy as np

# ============================================================
# UI CLICKING FOR DESKMATEAI
# Handles all mouse and UI interaction
# Click elements by voice description using EasyOCR
# Screenshots taken in RAM only - never saved to disk
# Works on active window only
# Three tier: pyautogui → pywinauto → ctypes
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.core.context import get_context_manager

# ── OCR Reader Singleton ──────────────────────────────────────

_ocr_reader = None

def _get_ocr_reader():
    """Get EasyOCR reader singleton"""
    global _ocr_reader
    if _ocr_reader is None:
        # print("[CLICKING] Loading EasyOCR reader...")
        try:
            import easyocr
            _ocr_reader = easyocr.Reader(['en'], gpu=False, verbose=False)
            # print("[CLICKING] ✅ EasyOCR reader loaded")
            log_info("EasyOCR reader loaded")
        except Exception as e:
            # print(f"[CLICKING] EasyOCR load failed: {e}")
            log_error(f"EasyOCR load failed: {e}")
    return _ocr_reader


# ── Click Element by Description ─────────────────────────────

def click_element(element_name):
    """
    Click UI element by voice description
    Uses EasyOCR to find text on screen
    Screenshot taken in RAM only - never saved
    Works on active window only
    """
    # print(f"[CLICKING] Clicking element: {element_name}")
    log_info(f"Clicking element: {element_name}")

    if not element_name:
        log_warning("No element name provided")
        return False

    # Layer 1: EasyOCR on active window
    success = _click_via_ocr(element_name)
    if success:
        # print(f"[CLICKING] ✅ Layer 1 click success: {element_name}")
        return True

    # Layer 2: pywinauto - find control by name
    success = _click_via_pywinauto(element_name)
    if success:
        # print(f"[CLICKING] ✅ Layer 2 click success: {element_name}")
        return True

    # print(f"[CLICKING] ❌ Element not found: {element_name}")
    log_warning(f"Element not found: {element_name}")
    return False


def _click_via_ocr(element_name):
    """
    Layer 1: Use EasyOCR to find and click element
    Screenshot in RAM only - deleted after use
    """
    # print(f"[CLICKING] OCR search for: {element_name}")
    screenshot = None
    img_array = None

    try:
        import pyautogui

        # Get active window region
        context = get_context_manager()
        region = context.get_active_window_region()

        # Refresh window info
        context.refresh_window_info()
        region = context.get_active_window_region()

        # Take screenshot in RAM only
        if region:
            left, top, right, bottom = region
            width = right - left
            height = bottom - top
            if width > 0 and height > 0:
                screenshot = pyautogui.screenshot(
                    region=(left, top, width, height)
                )
                # print(f"[CLICKING] Screenshot of active window: {width}x{height}")
            else:
                screenshot = pyautogui.screenshot()
                region = None
        else:
            screenshot = pyautogui.screenshot()
            region = None

        # Convert to numpy array in RAM
        img_array = np.array(screenshot)

        # Delete screenshot object immediately
        del screenshot
        screenshot = None

        # Get OCR reader
        reader = _get_ocr_reader()
        if not reader:
            # print("[CLICKING] OCR reader not available")
            if img_array is not None:
                del img_array
            return False

        # Run OCR
        # print("[CLICKING] Running OCR...")
        results = reader.readtext(img_array)
        # print(f"[CLICKING] OCR found {len(results)} text elements")

        # Delete image array immediately after OCR
        del img_array
        img_array = None

        # Find best match
        best_match = None
        best_score = 0
        element_lower = element_name.lower().strip()

        for (bbox, text, confidence) in results:
            text_lower = text.lower().strip()

            # Check exact match
            if element_lower == text_lower:
                best_match = (bbox, text, confidence)
                best_score = 1.0
                break

            # Check partial match
            if element_lower in text_lower or text_lower in element_lower:
                score = confidence * (
                    len(element_lower) / max(len(text_lower), len(element_lower))
                )
                if score > best_score:
                    best_score = score
                    best_match = (bbox, text, confidence)

        if best_match and best_score > 0.3:
            bbox, text, confidence = best_match
            # print(f"[CLICKING] Found: '{text}' (confidence: {confidence:.2f})")

            # Calculate center coordinates
            x_center = int((bbox[0][0] + bbox[2][0]) / 2)
            y_center = int((bbox[0][1] + bbox[2][1]) / 2)

            # Convert to screen coordinates if using window region
            if region:
                left, top, right, bottom = region
                x_center += left
                y_center += top

            # print(f"[CLICKING] Clicking at: ({x_center}, {y_center})")
            log_debug(f"Clicking at ({x_center}, {y_center}) for '{text}'")

            pyautogui.click(x_center, y_center)
            time.sleep(0.2)

            # print(f"[CLICKING] ✅ Clicked: '{text}'")
            return True

        # print(f"[CLICKING] Element not found by OCR: {element_name}")
        return False

    except Exception as e:
        # Ensure cleanup on error
        if screenshot is not None:
            del screenshot
        if img_array is not None:
            del img_array
        # print(f"[CLICKING] OCR click failed: {e}")
        log_error(f"OCR click failed: {e}")
        return False


def _click_via_pywinauto(element_name):
    """Layer 2: Use pywinauto to find control"""
    # print(f"[CLICKING] pywinauto search for: {element_name}")
    try:
        from pywinauto import Desktop
        import win32gui

        # Get active window
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)

        if not title:
            return False

        # Find window in pywinauto
        desktop = Desktop(backend="uia")
        windows = desktop.windows()

        target_window = None
        for window in windows:
            if title.lower() in window.window_text().lower():
                target_window = window
                break

        if not target_window:
            # print(f"[CLICKING] pywinauto window not found: {title}")
            return False

        # Search for control by name
        try:
            control = target_window.child_window(
                title=element_name,
                found_index=0
            )
            if control.exists():
                control.click_input()
                # print(f"[CLICKING] ✅ pywinauto clicked: {element_name}")
                log_debug(f"pywinauto clicked: {element_name}")
                return True
        except:
            pass

        # Try by partial name
        try:
            controls = target_window.descendants()
            for ctrl in controls:
                ctrl_text = ctrl.window_text().lower()
                if element_name.lower() in ctrl_text:
                    ctrl.click_input()
                    # print(f"[CLICKING] ✅ pywinauto partial click: {ctrl_text}")
                    log_debug(f"pywinauto partial click: {ctrl_text}")
                    return True
        except:
            pass

        # print(f"[CLICKING] pywinauto control not found: {element_name}")
        return False

    except Exception as e:
        # print(f"[CLICKING] pywinauto click failed: {e}")
        log_error(f"pywinauto click failed: {e}")
        return False


# ── Basic Mouse Operations ────────────────────────────────────

def left_click(x=None, y=None):
    """Left click at position or current position"""
    # print(f"[CLICKING] Left click: ({x}, {y})")
    log_info(f"Left click at ({x}, {y})")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        if x is not None and y is not None:
            pyautogui.click(x, y)
        else:
            pyautogui.click()
        # print("[CLICKING] ✅ Left clicked")
        return True
    except Exception as e:
        # print(f"[CLICKING] Left click failed: {e}")
        log_error(f"Left click failed: {e}")
        return False


def right_click(x=None, y=None):
    """Right click at position or current position"""
    # print(f"[CLICKING] Right click: ({x}, {y})")
    log_info(f"Right click at ({x}, {y})")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        if x is not None and y is not None:
            pyautogui.rightClick(x, y)
        else:
            pyautogui.rightClick()
        # print("[CLICKING] ✅ Right clicked")
        return True
    except Exception as e:
        # print(f"[CLICKING] Right click failed: {e}")
        log_error(f"Right click failed: {e}")
        return False


def double_click(x=None, y=None):
    """Double click at position"""
    # print(f"[CLICKING] Double click: ({x}, {y})")
    log_info(f"Double click at ({x}, {y})")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        if x is not None and y is not None:
            pyautogui.doubleClick(x, y)
        else:
            pyautogui.doubleClick()
        # print("[CLICKING] ✅ Double clicked")
        return True
    except Exception as e:
        # print(f"[CLICKING] Double click failed: {e}")
        log_error(f"Double click failed: {e}")
        return False


# ── Mouse Movement ────────────────────────────────────────────

def move_mouse_up(pixels=100):
    """Move mouse up"""
    # print(f"[CLICKING] Move mouse up: {pixels}px")
    log_info(f"Mouse up {pixels}px")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveRel(0, -pixels, duration=0.2)
        # print("[CLICKING] ✅ Mouse moved up")
        return True
    except Exception as e:
        # print(f"[CLICKING] Mouse up failed: {e}")
        log_error(f"Mouse up failed: {e}")
        return False


def move_mouse_down(pixels=100):
    """Move mouse down"""
    # print(f"[CLICKING] Move mouse down: {pixels}px")
    log_info(f"Mouse down {pixels}px")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveRel(0, pixels, duration=0.2)
        # print("[CLICKING] ✅ Mouse moved down")
        return True
    except Exception as e:
        # print(f"[CLICKING] Mouse down failed: {e}")
        log_error(f"Mouse down failed: {e}")
        return False


def move_mouse_left(pixels=100):
    """Move mouse left"""
    # print(f"[CLICKING] Move mouse left: {pixels}px")
    log_info(f"Mouse left {pixels}px")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveRel(-pixels, 0, duration=0.2)
        # print("[CLICKING] ✅ Mouse moved left")
        return True
    except Exception as e:
        # print(f"[CLICKING] Mouse left failed: {e}")
        log_error(f"Mouse left failed: {e}")
        return False


def move_mouse_right(pixels=100):
    """Move mouse right"""
    # print(f"[CLICKING] Move mouse right: {pixels}px")
    log_info(f"Mouse right {pixels}px")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveRel(pixels, 0, duration=0.2)
        # print("[CLICKING] ✅ Mouse moved right")
        return True
    except Exception as e:
        # print(f"[CLICKING] Mouse right failed: {e}")
        log_error(f"Mouse right failed: {e}")
        return False


def move_mouse_to(x, y):
    """Move mouse to specific position"""
    # print(f"[CLICKING] Move mouse to: ({x}, {y})")
    log_info(f"Mouse to ({x}, {y})")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.moveTo(x, y, duration=0.3)
        # print(f"[CLICKING] ✅ Mouse moved to ({x}, {y})")
        return True
    except Exception as e:
        # print(f"[CLICKING] Mouse move failed: {e}")
        log_error(f"Mouse move failed: {e}")
        return False


# ── Drag and Drop ─────────────────────────────────────────────

def drag_to(start_x, start_y, end_x, end_y):
    """Drag from start to end position"""
    # print(f"[CLICKING] Drag: ({start_x},{start_y}) → ({end_x},{end_y})")
    log_info(f"Drag from ({start_x},{start_y}) to ({end_x},{end_y})")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.drag(
            start_x, start_y,
            end_x - start_x,
            end_y - start_y,
            duration=0.5,
            button='left'
        )
        # print("[CLICKING] ✅ Drag completed")
        return True
    except Exception as e:
        # print(f"[CLICKING] Drag failed: {e}")
        log_error(f"Drag failed: {e}")
        return False


# ── Scroll ────────────────────────────────────────────────────

def scroll_up(clicks=3):
    """Scroll up"""
    # print(f"[CLICKING] Scroll up: {clicks} clicks")
    log_info(f"Scroll up {clicks}")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.scroll(clicks)
        # print("[CLICKING] ✅ Scrolled up")
        log_debug(f"Scrolled up {clicks}")
        return True
    except Exception as e:
        # print(f"[CLICKING] Scroll up failed: {e}")
        log_error(f"Scroll up failed: {e}")
        return False


def scroll_down(clicks=3):
    """Scroll down"""
    # print(f"[CLICKING] Scroll down: {clicks} clicks")
    log_info(f"Scroll down {clicks}")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.scroll(-clicks)
        # print("[CLICKING] ✅ Scrolled down")
        log_debug(f"Scrolled down {clicks}")
        return True
    except Exception as e:
        # print(f"[CLICKING] Scroll down failed: {e}")
        log_error(f"Scroll down failed: {e}")
        return False


def scroll_to_top():
    """Scroll to top of page"""
    # print("[CLICKING] Scroll to top...")
    log_info("Scroll to top")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'home')
        # print("[CLICKING] ✅ Scrolled to top")
        return True
    except Exception as e:
        # print(f"[CLICKING] Scroll to top failed: {e}")
        log_error(f"Scroll to top failed: {e}")
        return False


def scroll_to_bottom():
    """Scroll to bottom of page"""
    # print("[CLICKING] Scroll to bottom...")
    log_info("Scroll to bottom")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'end')
        # print("[CLICKING] ✅ Scrolled to bottom")
        return True
    except Exception as e:
        # print(f"[CLICKING] Scroll to bottom failed: {e}")
        log_error(f"Scroll to bottom failed: {e}")
        return False


# ── Zoom ──────────────────────────────────────────────────────

def zoom_in():
    """Zoom in"""
    # print("[CLICKING] Zoom in...")
    log_info("Zoom in")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', '+')
        # print("[CLICKING] ✅ Zoomed in")
        log_debug("Zoomed in")
        return True
    except Exception as e:
        # print(f"[CLICKING] Zoom in failed: {e}")
        log_error(f"Zoom in failed: {e}")
        return False


def zoom_out():
    """Zoom out"""
    # print("[CLICKING] Zoom out...")
    log_info("Zoom out")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', '-')
        # print("[CLICKING] ✅ Zoomed out")
        log_debug("Zoomed out")
        return True
    except Exception as e:
        # print(f"[CLICKING] Zoom out failed: {e}")
        log_error(f"Zoom out failed: {e}")
        return False


def reset_zoom():
    """Reset zoom to 100%"""
    # print("[CLICKING] Reset zoom...")
    log_info("Reset zoom")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', '0')
        # print("[CLICKING] ✅ Zoom reset")
        return True
    except Exception as e:
        # print(f"[CLICKING] Reset zoom failed: {e}")
        log_error(f"Reset zoom failed: {e}")
        return False


# ── Get Mouse Position ────────────────────────────────────────

def get_mouse_position():
    """Get current mouse position"""
    # print("[CLICKING] Getting mouse position...")
    try:
        import pyautogui
        x, y = pyautogui.position()
        # print(f"[CLICKING] Mouse position: ({x}, {y})")
        return x, y
    except Exception as e:
        # print(f"[CLICKING] Get position failed: {e}")
        log_error(f"Get mouse position failed: {e}")
        return None, None


# ── Screen Info ───────────────────────────────────────────────

def get_screen_size():
    """Get screen dimensions"""
    # print("[CLICKING] Getting screen size...")
    try:
        import pyautogui
        width, height = pyautogui.size()
        # print(f"[CLICKING] Screen size: {width}x{height}")
        return width, height
    except Exception as e:
        # print(f"[CLICKING] Get screen size failed: {e}")
        log_error(f"Get screen size failed: {e}")
        return None, None


def get_screen_center():
    """Get screen center coordinates"""
    # print("[CLICKING] Getting screen center...")
    width, height = get_screen_size()
    if width and height:
        return width // 2, height // 2
    return None, None