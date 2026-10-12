# DeskmateAI/backend/automation/app_workflows.py

import os
import sys
import time

# ============================================================
# APP WORKFLOWS FOR DESKMATEAI
# Handles multi-step automation workflows
# Window management, screenshots, complex operations
# Three tier: pyautogui → pywinauto → ctypes
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Window Management ─────────────────────────────────────────

def minimize_window():
    """Minimize active window"""
    # print("[WORKFLOW] Minimizing window...")
    log_info("Minimizing window")
    try:
        # Layer 1: pyautogui
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'down')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Window minimized via Win+Down")
        log_debug("Window minimized via Win+Down")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Layer 1 minimize failed: {e}")
        log_warning(f"pyautogui minimize failed: {e}")
        return _minimize_via_pywinauto()


def _minimize_via_pywinauto():
    """Layer 2: Minimize via pywinauto"""
    # print("[WORKFLOW] Layer 2 minimize - pywinauto...")
    try:
        import win32gui
        from pywinauto import Desktop

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)

        if title:
            desktop = Desktop(backend="uia")
            for window in desktop.windows():
                if title.lower() in window.window_text().lower():
                    window.minimize()
                    # print("[WORKFLOW] ✅ Minimized via pywinauto")
                    log_debug("Window minimized via pywinauto")
                    return True
        return False
    except Exception as e:
        # print(f"[WORKFLOW] Layer 2 minimize failed: {e}")
        log_error(f"pywinauto minimize failed: {e}")
        return False


def maximize_window():
    """Maximize active window"""
    # print("[WORKFLOW] Maximizing window...")
    log_info("Maximizing window")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'up')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Window maximized")
        log_debug("Window maximized")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Layer 1 maximize failed: {e}")
        log_warning(f"pyautogui maximize failed: {e}")
        return _maximize_via_pywinauto()


def _maximize_via_pywinauto():
    """Layer 2: Maximize via pywinauto"""
    # print("[WORKFLOW] Layer 2 maximize - pywinauto...")
    try:
        import win32gui
        from pywinauto import Desktop

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)

        if title:
            desktop = Desktop(backend="uia")
            for window in desktop.windows():
                if title.lower() in window.window_text().lower():
                    window.maximize()
                    # print("[WORKFLOW] ✅ Maximized via pywinauto")
                    log_debug("Window maximized via pywinauto")
                    return True
        return False
    except Exception as e:
        # print(f"[WORKFLOW] Layer 2 maximize failed: {e}")
        log_error(f"pywinauto maximize failed: {e}")
        return False


def restore_window():
    """Restore window to normal size"""
    # print("[WORKFLOW] Restoring window...")
    log_info("Restoring window")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'down')
        time.sleep(0.2)
        pyautogui.hotkey('win', 'down')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Window restored")
        log_debug("Window restored")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Restore failed: {e}")
        log_warning(f"Restore window failed: {e}")
        return _restore_via_pywinauto()


def _restore_via_pywinauto():
    """Layer 2: Restore via pywinauto"""
    # print("[WORKFLOW] Layer 2 restore - pywinauto...")
    try:
        import win32gui
        from pywinauto import Desktop

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)

        if title:
            desktop = Desktop(backend="uia")
            for window in desktop.windows():
                if title.lower() in window.window_text().lower():
                    window.restore()
                    # print("[WORKFLOW] ✅ Restored via pywinauto")
                    log_debug("Window restored via pywinauto")
                    return True
        return False
    except Exception as e:
        # print(f"[WORKFLOW] Layer 2 restore failed: {e}")
        log_error(f"pywinauto restore failed: {e}")
        return False


def close_window():
    """Close active window"""
    # print("[WORKFLOW] Closing window...")
    log_info("Closing window")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('alt', 'f4')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Window closed")
        log_debug("Window closed via Alt+F4")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Close window failed: {e}")
        log_warning(f"pyautogui close window failed: {e}")
        return _close_via_pywinauto()


def _close_via_pywinauto():
    """Layer 2: Close via pywinauto"""
    # print("[WORKFLOW] Layer 2 close - pywinauto...")
    try:
        import win32gui
        from pywinauto import Desktop

        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)

        if title:
            desktop = Desktop(backend="uia")
            for window in desktop.windows():
                if title.lower() in window.window_text().lower():
                    window.close()
                    # print("[WORKFLOW] ✅ Closed via pywinauto")
                    log_debug("Window closed via pywinauto")
                    return True
        return False
    except Exception as e:
        # print(f"[WORKFLOW] Layer 2 close failed: {e}")
        log_error(f"pywinauto close window failed: {e}")
        return False


def switch_window(app_name=None):
    """
    Switch to specific app window
    or cycle through windows with Alt+Tab
    """
    # print(f"[WORKFLOW] Switching window: {app_name}")
    log_info(f"Switching window: {app_name}")

    if app_name:
        # Switch to specific app
        return _switch_to_specific(app_name)
    else:
        # Cycle through windows
        try:
            import pyautogui
            pyautogui.hotkey('alt', 'tab')
            time.sleep(0.3)
            # print("[WORKFLOW] ✅ Window switched via Alt+Tab")
            return True
        except Exception as e:
            # print(f"[WORKFLOW] Switch window failed: {e}")
            log_error(f"Switch window failed: {e}")
            return False


def _switch_to_specific(app_name):
    """Switch to specific application window"""
    # print(f"[WORKFLOW] Switching to specific: {app_name}")
    try:
        import win32gui

        app_lower = app_name.lower()
        found_hwnd = None

        def callback(hwnd, _):
            nonlocal found_hwnd
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_lower in title:
                    found_hwnd = hwnd

        win32gui.EnumWindows(callback, None)

        if found_hwnd:
            win32gui.SetForegroundWindow(found_hwnd)
            time.sleep(0.3)
            # print(f"[WORKFLOW] ✅ Switched to: {app_name}")
            log_debug(f"Switched to: {app_name}")
            return True

        # print(f"[WORKFLOW] Window not found: {app_name}")
        log_warning(f"Window not found: {app_name}")
        return False

    except Exception as e:
        # print(f"[WORKFLOW] Switch to specific failed: {e}")
        log_error(f"Switch to specific window failed: {e}")
        return False


def snap_window_left():
    """Snap window to left half of screen"""
    # print("[WORKFLOW] Snapping window left...")
    log_info("Snap window left")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'left')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Window snapped left")
        log_debug("Window snapped left")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Snap left failed: {e}")
        log_error(f"Snap left failed: {e}")
        return False


def snap_window_right():
    """Snap window to right half of screen"""
    # print("[WORKFLOW] Snapping window right...")
    log_info("Snap window right")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'right')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Window snapped right")
        log_debug("Window snapped right")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Snap right failed: {e}")
        log_error(f"Snap right failed: {e}")
        return False


def show_desktop():
    """Show desktop (minimize all windows)"""
    # print("[WORKFLOW] Showing desktop...")
    log_info("Show desktop")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'd')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Desktop shown")
        log_debug("Desktop shown")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Show desktop failed: {e}")
        log_error(f"Show desktop failed: {e}")
        return False


def show_all_windows():
    """Show all open windows (Task View)"""
    # print("[WORKFLOW] Showing all windows...")
    log_info("Show all windows")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.hotkey('win', 'tab')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Task view opened")
        log_debug("Task view opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Show all windows failed: {e}")
        log_error(f"Show all windows failed: {e}")
        return False


# ── Screenshot ────────────────────────────────────────────────

def take_screenshot():
    """
    Take screenshot and save to Desktop
    Uses timestamp for unique filename
    """
    # print("[WORKFLOW] Taking screenshot...")
    log_info("Taking screenshot")
    try:
        import pyautogui
        from datetime import datetime

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.makedirs(desktop, exist_ok=True)
        filename = os.path.join(desktop, f"screenshot_{timestamp}.png")

        screenshot = pyautogui.screenshot()
        screenshot.save(filename)
        del screenshot

        # print(f"[WORKFLOW] ✅ Screenshot saved: {filename}")
        log_info(f"Screenshot saved: {filename}")
        return True

    except Exception as e:
        # print(f"[WORKFLOW] Screenshot failed: {e}")
        log_error(f"Screenshot failed: {e}")
        return _screenshot_via_win_key()


def _screenshot_via_win_key():
    """Fallback screenshot via Win+PrtSc"""
    # print("[WORKFLOW] Fallback screenshot via Win+PrtSc...")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'prtsc')
        time.sleep(0.5)
        # print("[WORKFLOW] ✅ Screenshot via Win+PrtSc")
        log_debug("Screenshot via Win+PrtSc")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Win+PrtSc failed: {e}")
        log_error(f"Win+PrtSc screenshot failed: {e}")
        return False


def take_region_screenshot():
    """Take screenshot of selected region via Win+Shift+S"""
    # print("[WORKFLOW] Region screenshot...")
    log_info("Region screenshot")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'shift', 's')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Snip tool opened")
        log_debug("Snip tool opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Region screenshot failed: {e}")
        log_error(f"Region screenshot failed: {e}")
        return False


# ── Virtual Desktops ──────────────────────────────────────────

def new_virtual_desktop():
    """Create new virtual desktop"""
    # print("[WORKFLOW] New virtual desktop...")
    log_info("New virtual desktop")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'ctrl', 'd')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ New virtual desktop created")
        log_debug("New virtual desktop created")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] New virtual desktop failed: {e}")
        log_error(f"New virtual desktop failed: {e}")
        return False


def next_virtual_desktop():
    """Switch to next virtual desktop"""
    # print("[WORKFLOW] Next virtual desktop...")
    log_info("Next virtual desktop")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'ctrl', 'right')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Next virtual desktop")
        log_debug("Next virtual desktop")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Next virtual desktop failed: {e}")
        log_error(f"Next virtual desktop failed: {e}")
        return False


def previous_virtual_desktop():
    """Switch to previous virtual desktop"""
    # print("[WORKFLOW] Previous virtual desktop...")
    log_info("Previous virtual desktop")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'ctrl', 'left')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Previous virtual desktop")
        log_debug("Previous virtual desktop")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Previous virtual desktop failed: {e}")
        log_error(f"Previous virtual desktop failed: {e}")
        return False


def close_virtual_desktop():
    """Close current virtual desktop"""
    # print("[WORKFLOW] Closing virtual desktop...")
    log_info("Close virtual desktop")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'ctrl', 'f4')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Virtual desktop closed")
        log_debug("Virtual desktop closed")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Close virtual desktop failed: {e}")
        log_error(f"Close virtual desktop failed: {e}")
        return False


# ── File Explorer Workflows ───────────────────────────────────

def open_file_explorer():
    """Open File Explorer"""
    # print("[WORKFLOW] Opening File Explorer...")
    log_info("Opening File Explorer")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'e')
        time.sleep(0.5)
        # print("[WORKFLOW] ✅ File Explorer opened")
        log_debug("File Explorer opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] File Explorer failed: {e}")
        log_error(f"File Explorer failed: {e}")
        return False


def open_downloads_folder():
    """Open Downloads folder"""
    # print("[WORKFLOW] Opening Downloads...")
    log_info("Opening Downloads folder")
    try:
        downloads = os.path.join(os.path.expanduser("~"), "Downloads")
        os.startfile(downloads)
        time.sleep(0.5)
        # print("[WORKFLOW] ✅ Downloads opened")
        log_debug("Downloads folder opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Downloads failed: {e}")
        log_error(f"Open downloads failed: {e}")
        return False


def open_documents_folder():
    """Open Documents folder"""
    # print("[WORKFLOW] Opening Documents...")
    log_info("Opening Documents folder")
    try:
        documents = os.path.join(os.path.expanduser("~"), "Documents")
        os.startfile(documents)
        time.sleep(0.5)
        # print("[WORKFLOW] ✅ Documents opened")
        log_debug("Documents folder opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Documents failed: {e}")
        log_error(f"Open documents failed: {e}")
        return False


def open_desktop_folder():
    """Open Desktop folder"""
    # print("[WORKFLOW] Opening Desktop...")
    log_info("Opening Desktop folder")
    try:
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        os.startfile(desktop)
        time.sleep(0.5)
        # print("[WORKFLOW] ✅ Desktop folder opened")
        log_debug("Desktop folder opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Desktop failed: {e}")
        log_error(f"Open desktop failed: {e}")
        return False


# ── System Dialogs ────────────────────────────────────────────

def open_run_dialog():
    """Open Run dialog"""
    # print("[WORKFLOW] Opening Run dialog...")
    log_info("Opening Run dialog")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'r')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Run dialog opened")
        log_debug("Run dialog opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Run dialog failed: {e}")
        log_error(f"Run dialog failed: {e}")
        return False


def open_settings():
    """Open Windows Settings"""
    # print("[WORKFLOW] Opening Settings...")
    log_info("Opening Windows Settings")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'i')
        time.sleep(0.5)
        # print("[WORKFLOW] ✅ Settings opened")
        log_debug("Settings opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Settings failed: {e}")
        log_error(f"Open settings failed: {e}")
        return False


def open_action_center():
    """Open Action Center / Notification panel"""
    # print("[WORKFLOW] Opening Action Center...")
    log_info("Opening Action Center")
    try:
        import pyautogui
        pyautogui.hotkey('win', 'a')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Action Center opened")
        log_debug("Action Center opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Action Center failed: {e}")
        log_error(f"Action Center failed: {e}")
        return False


def open_search():
    """Open Windows Search"""
    # print("[WORKFLOW] Opening Search...")
    log_info("Opening Windows Search")
    try:
        import pyautogui
        pyautogui.hotkey('win', 's')
        time.sleep(0.3)
        # print("[WORKFLOW] ✅ Search opened")
        log_debug("Windows Search opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Search failed: {e}")
        log_error(f"Open search failed: {e}")
        return False


# ── Multi-Step Workflows ──────────────────────────────────────

def open_new_document_word():
    """Open Word and create new document"""
    # print("[WORKFLOW] Opening new Word document...")
    log_info("Opening new Word document")
    try:
        from backend.automation.app_launcher import open_app
        success = open_app("winword")
        if success:
            time.sleep(2.0)
            import pyautogui
            # Press Enter to create new blank document if prompted
            pyautogui.press('enter')
            # print("[WORKFLOW] ✅ New Word document opened")
            log_info("New Word document opened")
        return success
    except Exception as e:
        # print(f"[WORKFLOW] Word open failed: {e}")
        log_error(f"Open new Word document failed: {e}")
        return False


def open_new_browser_tab_and_search(query):
    """Open new tab and search"""
    # print(f"[WORKFLOW] New tab + search: {query}")
    log_info(f"New tab + search: {query}")
    try:
        from backend.automation.web_interaction import new_tab, search
        new_tab()
        time.sleep(0.3)
        search(query)
        # print(f"[WORKFLOW] ✅ New tab + search: {query}")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] New tab + search failed: {e}")
        log_error(f"New tab + search failed: {e}")
        return False


def compose_email():
    """Open email client and compose new email"""
    # print("[WORKFLOW] Composing email...")
    log_info("Composing email")
    try:
        from backend.automation.app_launcher import open_app
        # Try to open default mail app
        os.startfile("mailto:")
        time.sleep(1.0)
        # print("[WORKFLOW] ✅ Email compose opened")
        log_info("Email compose opened")
        return True
    except Exception as e:
        # print(f"[WORKFLOW] Compose email failed: {e}")
        log_error(f"Compose email failed: {e}")
        return False


def get_active_window_title():
    """Get title of currently active window"""
    # print("[WORKFLOW] Getting active window title...")
    try:
        import win32gui
        hwnd = win32gui.GetForegroundWindow()
        title = win32gui.GetWindowText(hwnd)
        # print(f"[WORKFLOW] Active window: {title}")
        return title
    except Exception as e:
        # print(f"[WORKFLOW] Get active window failed: {e}")
        log_error(f"Get active window title failed: {e}")
        return None


def get_all_open_windows():
    """Get list of all visible window titles"""
    # print("[WORKFLOW] Getting all open windows...")
    try:
        import win32gui
        windows = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    windows.append(title)

        win32gui.EnumWindows(callback, None)
        # print(f"[WORKFLOW] Open windows: {len(windows)}")
        return windows
    except Exception as e:
        # print(f"[WORKFLOW] Get windows failed: {e}")
        log_error(f"Get all windows failed: {e}")
        return []