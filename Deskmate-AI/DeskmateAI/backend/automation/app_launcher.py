# DeskmateAI/backend/automation/app_launcher.py

import os
import sys
import time
import subprocess

# ============================================================
# APP LAUNCHER FOR DESKMATEAI
# Handles opening and closing applications
# Three tier approach:
# Layer 1: pyautogui (Win key + search)
# Layer 2: pywinauto (Windows API)
# Layer 3: ctypes / os.startfile
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── App Name to Executable Mapping ───────────────────────────

APP_COMMANDS = {
    # Browsers
    "chrome":       "chrome",
    "msedge":       "msedge",
    "firefox":      "firefox",
    "opera":        "opera",
    "brave":        "brave",

    # Microsoft Office
    "winword":      "winword",
    "excel":        "excel",
    "powerpnt":     "powerpnt",
    "outlook":      "outlook",
    "onenote":      "onenote",
    "access":       "msaccess",

    # System Apps
    "notepad":      "notepad",
    "mspaint":      "mspaint",
    "calc":         "calc",
    "explorer":     "explorer",
    "taskmgr":      "taskmgr",
    "control":      "control",
    "cmd":          "cmd",
    "powershell":   "powershell",
    "regedit":      "regedit",
    "mmc":          "mmc",

    # Media
    "vlc":          "vlc",
    "spotify":      "spotify",
    "groove":       "mswindowsmusic",
    "photos":       "ms-photos:",
    "movies":       "mswindowsvideo",

    # Communication
    "teams":        "teams",
    "zoom":         "zoom",
    "skype":        "skype",
    "discord":      "discord",
    "whatsapp":     "whatsapp",
    "telegram":     "telegram",
    "slack":        "slack",

    # Development
    "code":         "code",
    "pycharm":      "pycharm",
    "android":      "studio",
    "git":          "git-bash",

    # Gaming
    "steam":        "steam",
    "epic":         "epicgameslauncher",

    # Settings
    "ms-settings:": "ms-settings:",

    # Creative
    "photoshop":    "photoshop",
    "premiere":     "premiere",
    "afterfx":      "afterfx",
    "illustrator":  "illustrator",
}

# Apps that use ms-settings: protocol
SETTINGS_APPS = {
    "settings":             "ms-settings:",
    "bluetooth":            "ms-settings:bluetooth",
    "wifi":                 "ms-settings:network-wifi",
    "display":              "ms-settings:display",
    "sound":                "ms-settings:sound",
    "notifications":        "ms-settings:notifications",
    "apps":                 "ms-settings:appsfeatures",
    "accounts":             "ms-settings:accounts",
    "time":                 "ms-settings:dateandtime",
    "region":               "ms-settings:regionformatting",
    "language":             "ms-settings:regionlanguage",
    "update":               "ms-settings:windowsupdate",
    "privacy":              "ms-settings:privacy",
    "storage":              "ms-settings:storagesense",
    "battery":              "ms-settings:batterysaver",
    "accessibility":        "ms-settings:easeofaccess",
}

# ── Open App ──────────────────────────────────────────────────

def open_app(app_name):
    """
    Open application by name
    Three tier: pyautogui → pywinauto → os.startfile
    """
    # print(f"[APP_LAUNCHER] Opening app: {app_name}")
    log_info(f"Opening app: {app_name}")

    if not app_name:
        log_warning("No app name provided")
        return False

    app_name = app_name.lower().strip()

    # Check if settings app
    if app_name in SETTINGS_APPS:
        return _open_settings_app(SETTINGS_APPS[app_name])

    # Layer 1: pyautogui
    success = _open_via_pyautogui(app_name)
    if success:
        # print(f"[APP_LAUNCHER] ✅ Layer 1 success: {app_name}")
        return True

    # Layer 2: os.startfile / subprocess
    success = _open_via_startfile(app_name)
    if success:
        # print(f"[APP_LAUNCHER] ✅ Layer 2 success: {app_name}")
        return True

    # Layer 3: pywinauto
    success = _open_via_pywinauto(app_name)
    if success:
        # print(f"[APP_LAUNCHER] ✅ Layer 3 success: {app_name}")
        return True

    # print(f"[APP_LAUNCHER] ❌ All layers failed for: {app_name}")
    log_error(f"Failed to open app: {app_name}")
    return False


def _open_via_pyautogui(app_name):
    """Layer 1: Use Windows search to open app"""
    # print(f"[APP_LAUNCHER] Layer 1 - pyautogui: {app_name}")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False

        # Press Windows key
        pyautogui.press('win')
        time.sleep(0.5)

        # Type app name
        pyautogui.write(app_name, interval=0.05)
        time.sleep(0.8)

        # Press Enter
        pyautogui.press('enter')
        time.sleep(1.0)

        # print(f"[APP_LAUNCHER] Layer 1 executed for: {app_name}")
        log_debug(f"pyautogui open: {app_name}")
        return True

    except Exception as e:
        # print(f"[APP_LAUNCHER] Layer 1 failed: {e}")
        log_warning(f"pyautogui open failed: {e}")
        return False


def _open_via_startfile(app_name):
    """Layer 2: Use os.startfile or subprocess"""
    # print(f"[APP_LAUNCHER] Layer 2 - startfile: {app_name}")
    try:
        # Get executable name
        executable = APP_COMMANDS.get(app_name, app_name)

        # Try ms-settings protocol
        if executable.startswith("ms-"):
            os.startfile(executable)
            # print(f"[APP_LAUNCHER] Layer 2 - ms-settings: {executable}")
            return True

        # Try direct startfile
        try:
            os.startfile(executable)
            # print(f"[APP_LAUNCHER] Layer 2 - startfile: {executable}")
            log_debug(f"startfile open: {executable}")
            return True
        except:
            pass

        # Try subprocess
        subprocess.Popen(
            executable,
            shell=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        # print(f"[APP_LAUNCHER] Layer 2 - subprocess: {executable}")
        log_debug(f"subprocess open: {executable}")
        return True

    except Exception as e:
        # print(f"[APP_LAUNCHER] Layer 2 failed: {e}")
        log_warning(f"startfile open failed: {e}")
        return False


def _open_via_pywinauto(app_name):
    """Layer 3: Use pywinauto Application"""
    # print(f"[APP_LAUNCHER] Layer 3 - pywinauto: {app_name}")
    try:
        from pywinauto import Application

        executable = APP_COMMANDS.get(app_name, app_name)

        app = Application().start(executable)
        time.sleep(1.0)
        # print(f"[APP_LAUNCHER] Layer 3 - pywinauto opened: {executable}")
        log_debug(f"pywinauto open: {executable}")
        return True

    except Exception as e:
        # print(f"[APP_LAUNCHER] Layer 3 failed: {e}")
        log_warning(f"pywinauto open failed: {e}")
        return False


def _open_settings_app(settings_url):
    """Open Windows Settings app"""
    # print(f"[APP_LAUNCHER] Opening settings: {settings_url}")
    try:
        os.startfile(settings_url)
        log_debug(f"Settings opened: {settings_url}")
        return True
    except Exception as e:
        # print(f"[APP_LAUNCHER] Settings open failed: {e}")
        log_error(f"Settings open failed: {e}")
        return False


# ── Close App ─────────────────────────────────────────────────

def close_app(app_name):
    """
    Close application by name
    Three tier: pyautogui → pywinauto → taskkill
    """
    # print(f"[APP_LAUNCHER] Closing app: {app_name}")
    log_info(f"Closing app: {app_name}")

    if not app_name:
        log_warning("No app name provided to close")
        return False

    app_name = app_name.lower().strip()

    # Layer 1: pyautogui - find and close active window
    success = _close_via_pyautogui(app_name)
    if success:
        # print(f"[APP_LAUNCHER] ✅ Layer 1 close success: {app_name}")
        return True

    # Layer 2: pywinauto - find window and close
    success = _close_via_pywinauto(app_name)
    if success:
        # print(f"[APP_LAUNCHER] ✅ Layer 2 close success: {app_name}")
        return True

    # Layer 3: taskkill
    success = _close_via_taskkill(app_name)
    if success:
        # print(f"[APP_LAUNCHER] ✅ Layer 3 close success: {app_name}")
        return True

    # print(f"[APP_LAUNCHER] ❌ All close layers failed: {app_name}")
    log_error(f"Failed to close app: {app_name}")
    return False


def _close_via_pyautogui(app_name):
    """Layer 1: Focus window then Alt+F4"""
    # print(f"[APP_LAUNCHER] Layer 1 close - pyautogui: {app_name}")
    try:
        import pyautogui
        import win32gui

        # Find window by app name
        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_name in title or _get_app_display_name(app_name) in title:
                    windows.append(hwnd)

        windows = []
        win32gui.EnumWindows(callback, windows)

        if windows:
            # Bring to front
            win32gui.SetForegroundWindow(windows[0])
            time.sleep(0.3)

            # Close with Alt+F4
            pyautogui.hotkey('alt', 'f4')
            time.sleep(0.5)
            # print(f"[APP_LAUNCHER] Layer 1 close executed: {app_name}")
            log_debug(f"pyautogui close: {app_name}")
            return True

        # print(f"[APP_LAUNCHER] Layer 1 - window not found: {app_name}")
        return False

    except Exception as e:
        # print(f"[APP_LAUNCHER] Layer 1 close failed: {e}")
        log_warning(f"pyautogui close failed: {e}")
        return False


def _close_via_pywinauto(app_name):
    """Layer 2: Use pywinauto to find and close"""
    # print(f"[APP_LAUNCHER] Layer 2 close - pywinauto: {app_name}")
    try:
        from pywinauto import Desktop

        display_name = _get_app_display_name(app_name)
        windows = Desktop(backend="uia").windows()

        for window in windows:
            title = window.window_text().lower()
            if app_name in title or display_name in title:
                window.close()
                time.sleep(0.5)
                # print(f"[APP_LAUNCHER] Layer 2 close success: {app_name}")
                log_debug(f"pywinauto close: {app_name}")
                return True

        # print(f"[APP_LAUNCHER] Layer 2 - window not found: {app_name}")
        return False

    except Exception as e:
        # print(f"[APP_LAUNCHER] Layer 2 close failed: {e}")
        log_warning(f"pywinauto close failed: {e}")
        return False


def _close_via_taskkill(app_name):
    """Layer 3: Force kill process"""
    # print(f"[APP_LAUNCHER] Layer 3 close - taskkill: {app_name}")
    try:
        executable = APP_COMMANDS.get(app_name, app_name)

        # Add .exe if not present
        if not executable.endswith('.exe'):
            executable_with_ext = executable + '.exe'
        else:
            executable_with_ext = executable

        result = subprocess.run(
            ['taskkill', '/F', '/IM', executable_with_ext],
            capture_output=True,
            text=True
        )

        if result.returncode == 0:
            # print(f"[APP_LAUNCHER] Layer 3 taskkill success: {executable_with_ext}")
            log_info(f"taskkill success: {executable_with_ext}")
            return True
        else:
            # print(f"[APP_LAUNCHER] Layer 3 taskkill failed: {result.stderr}")
            return False

    except Exception as e:
        # print(f"[APP_LAUNCHER] Layer 3 close failed: {e}")
        log_error(f"taskkill failed: {e}")
        return False


# ── Switch to App ─────────────────────────────────────────────

def switch_to_app(app_name):
    """
    Switch focus to already open application
    """
    # print(f"[APP_LAUNCHER] Switching to app: {app_name}")
    log_info(f"Switching to: {app_name}")

    try:
        import win32gui

        app_name = app_name.lower().strip()
        display_name = _get_app_display_name(app_name)

        def callback(hwnd, windows):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_name in title or display_name in title:
                    windows.append(hwnd)

        windows = []
        win32gui.EnumWindows(callback, windows)

        if windows:
            win32gui.SetForegroundWindow(windows[0])
            time.sleep(0.3)
            # print(f"[APP_LAUNCHER] ✅ Switched to: {app_name}")
            log_debug(f"Switched to: {app_name}")
            return True

        # App not open, open it
        # print(f"[APP_LAUNCHER] App not open, opening: {app_name}")
        return open_app(app_name)

    except Exception as e:
        # print(f"[APP_LAUNCHER] Switch failed: {e}")
        log_error(f"Switch to app failed: {e}")
        return False


# ── List Open Apps ────────────────────────────────────────────

def get_open_apps():
    """Get list of currently open applications"""
    # print("[APP_LAUNCHER] Getting open apps...")
    try:
        import win32gui

        open_apps = []

        def callback(hwnd, apps):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd)
                if title:
                    apps.append(title)

        win32gui.EnumWindows(callback, open_apps)
        # print(f"[APP_LAUNCHER] Open apps: {len(open_apps)}")
        return open_apps

    except Exception as e:
        # print(f"[APP_LAUNCHER] Error getting open apps: {e}")
        log_error(f"Error getting open apps: {e}")
        return []


# ── Helper Functions ──────────────────────────────────────────

def _get_app_display_name(app_name):
    """Get human readable display name for app"""
    display_names = {
        "chrome":       "google chrome",
        "msedge":       "microsoft edge",
        "firefox":      "mozilla firefox",
        "winword":      "microsoft word",
        "excel":        "microsoft excel",
        "powerpnt":     "microsoft powerpoint",
        "outlook":      "microsoft outlook",
        "notepad":      "notepad",
        "mspaint":      "paint",
        "calc":         "calculator",
        "explorer":     "file explorer",
        "taskmgr":      "task manager",
        "code":         "visual studio code",
        "vlc":          "vlc media player",
        "spotify":      "spotify",
        "teams":        "microsoft teams",
        "zoom":         "zoom",
        "discord":      "discord",
        "whatsapp":     "whatsapp",
        "telegram":     "telegram",
        "cmd":          "command prompt",
        "powershell":   "windows powershell",
        "steam":        "steam",
    }
    return display_names.get(app_name.lower(), app_name)


def is_app_open(app_name):
    """Check if app is currently open"""
    # print(f"[APP_LAUNCHER] Checking if open: {app_name}")
    try:
        import win32gui

        app_name = app_name.lower().strip()
        display_name = _get_app_display_name(app_name)
        found = [False]

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if app_name in title or display_name in title:
                    found[0] = True

        win32gui.EnumWindows(callback, None)
        # print(f"[APP_LAUNCHER] App open status: {app_name} = {found[0]}")
        return found[0]

    except Exception as e:
        # print(f"[APP_LAUNCHER] Error checking app: {e}")
        log_error(f"Error checking app open: {e}")
        return False