# DeskmateAI/backend/automation/web_interaction.py

import os
import sys
import time

# ============================================================
# WEB INTERACTION FOR DESKMATEAI
# Handles all browser and web related actions
# Search, navigation, tabs, bookmarks
# Three tier: pyautogui → pywinauto → ctypes
# Works with Chrome, Firefox, Edge, Opera, Brave
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Search ────────────────────────────────────────────────────

def search(query):
    """
    Search on Google
    Opens browser if not open
    Three tier approach
    """
    # print(f"[WEB] Searching for: {query}")
    log_info(f"Searching: {query}")

    if not query:
        log_warning("Empty search query")
        return False

    # Layer 1: pyautogui
    success = _search_via_pyautogui(query)
    if success:
        # print(f"[WEB] ✅ Layer 1 search success: {query}")
        return True

    # Layer 2: pywinauto
    success = _search_via_pywinauto(query)
    if success:
        # print(f"[WEB] ✅ Layer 2 search success: {query}")
        return True

    # Layer 3: os.startfile with URL
    success = _search_via_url(query)
    if success:
        # print(f"[WEB] ✅ Layer 3 search success: {query}")
        return True

    # print(f"[WEB] ❌ All search layers failed: {query}")
    log_error(f"Search failed: {query}")
    return False


def _search_via_pyautogui(query):
    """Layer 1: Use address bar to search"""
    # print(f"[WEB] Layer 1 search - pyautogui: {query}")
    try:
        import pyautogui

        # Focus address bar with Ctrl+L
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)

        # Clear and type search URL
        pyautogui.hotkey('ctrl', 'a')
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        pyautogui.write(search_url, interval=0.03)
        time.sleep(0.2)

        # Press Enter
        pyautogui.press('enter')
        time.sleep(0.5)

        # print(f"[WEB] Layer 1 search executed: {query}")
        log_debug(f"pyautogui search: {query}")
        return True

    except Exception as e:
        # print(f"[WEB] Layer 1 search failed: {e}")
        log_warning(f"pyautogui search failed: {e}")
        return False


def _search_via_pywinauto(query):
    """Layer 2: Use pywinauto to interact with browser"""
    # print(f"[WEB] Layer 2 search - pywinauto: {query}")
    try:
        from pywinauto import Desktop

        # Find browser window
        browser_titles = ['chrome', 'firefox', 'edge', 'opera', 'brave']
        browser_window = None

        windows = Desktop(backend="uia").windows()
        for window in windows:
            title = window.window_text().lower()
            for browser in browser_titles:
                if browser in title:
                    browser_window = window
                    break
            if browser_window:
                break

        if browser_window:
            browser_window.set_focus()
            time.sleep(0.3)

            import pyautogui
            pyautogui.hotkey('ctrl', 'l')
            time.sleep(0.3)

            search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
            pyautogui.write(search_url, interval=0.03)
            pyautogui.press('enter')

            # print(f"[WEB] Layer 2 search executed: {query}")
            log_debug(f"pywinauto search: {query}")
            return True

        # print(f"[WEB] Layer 2 - no browser found")
        return False

    except Exception as e:
        # print(f"[WEB] Layer 2 search failed: {e}")
        log_warning(f"pywinauto search failed: {e}")
        return False


def _search_via_url(query):
    """Layer 3: Open search URL directly"""
    # print(f"[WEB] Layer 3 search - URL: {query}")
    try:
        search_url = f"https://www.google.com/search?q={query.replace(' ', '+')}"
        os.startfile(search_url)
        time.sleep(1.0)
        # print(f"[WEB] Layer 3 search executed: {query}")
        log_debug(f"URL search: {query}")
        return True
    except Exception as e:
        # print(f"[WEB] Layer 3 search failed: {e}")
        log_error(f"URL search failed: {e}")
        return False


# ── YouTube Search ────────────────────────────────────────────

def search_youtube(query):
    """Search on YouTube"""
    # print(f"[WEB] YouTube search: {query}")
    log_info(f"YouTube search: {query}")
    try:
        youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"

        # Try address bar first
        import pyautogui
        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.write(youtube_url, interval=0.03)
        pyautogui.press('enter')
        # print(f"[WEB] ✅ YouTube search: {query}")
        return True
    except Exception as e:
        # Fallback to startfile
        try:
            youtube_url = f"https://www.youtube.com/results?search_query={query.replace(' ', '+')}"
            os.startfile(youtube_url)
            return True
        except Exception as e2:
            # print(f"[WEB] YouTube search failed: {e2}")
            log_error(f"YouTube search failed: {e2}")
            return False


# ── Tab Management ────────────────────────────────────────────

def new_tab():
    """Open new browser tab"""
    # print("[WEB] Opening new tab...")
    log_info("Opening new tab")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 't')
        time.sleep(0.3)
        # print("[WEB] ✅ New tab opened")
        log_debug("New tab opened")
        return True
    except Exception as e:
        # print(f"[WEB] New tab failed: {e}")
        log_error(f"New tab failed: {e}")
        return False


def close_tab():
    """Close current browser tab"""
    # print("[WEB] Closing tab...")
    log_info("Closing tab")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'w')
        time.sleep(0.3)
        # print("[WEB] ✅ Tab closed")
        log_debug("Tab closed")
        return True
    except Exception as e:
        # print(f"[WEB] Close tab failed: {e}")
        log_error(f"Close tab failed: {e}")
        return False


def next_tab():
    """Switch to next browser tab"""
    # print("[WEB] Next tab...")
    log_info("Next tab")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'tab')
        time.sleep(0.2)
        # print("[WEB] ✅ Next tab")
        return True
    except Exception as e:
        # print(f"[WEB] Next tab failed: {e}")
        log_error(f"Next tab failed: {e}")
        return False


def previous_tab():
    """Switch to previous browser tab"""
    # print("[WEB] Previous tab...")
    log_info("Previous tab")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'shift', 'tab')
        time.sleep(0.2)
        # print("[WEB] ✅ Previous tab")
        return True
    except Exception as e:
        # print(f"[WEB] Previous tab failed: {e}")
        log_error(f"Previous tab failed: {e}")
        return False


def reopen_closed_tab():
    """Reopen last closed tab"""
    # print("[WEB] Reopening closed tab...")
    log_info("Reopening closed tab")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'shift', 't')
        time.sleep(0.3)
        # print("[WEB] ✅ Closed tab reopened")
        return True
    except Exception as e:
        # print(f"[WEB] Reopen tab failed: {e}")
        log_error(f"Reopen tab failed: {e}")
        return False


# ── Navigation ────────────────────────────────────────────────

def go_back():
    """Navigate back in browser"""
    # print("[WEB] Going back...")
    log_info("Browser back")
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'left')
        time.sleep(0.3)
        # print("[WEB] ✅ Went back")
        return True
    except Exception as e:
        # print(f"[WEB] Go back failed: {e}")
        log_error(f"Go back failed: {e}")
        return False


def go_forward():
    """Navigate forward in browser"""
    # print("[WEB] Going forward...")
    log_info("Browser forward")
    try:
        import pyautogui
        pyautogui.hotkey('alt', 'right')
        time.sleep(0.3)
        # print("[WEB] ✅ Went forward")
        return True
    except Exception as e:
        # print(f"[WEB] Go forward failed: {e}")
        log_error(f"Go forward failed: {e}")
        return False


def refresh_page():
    """Refresh current page"""
    # print("[WEB] Refreshing page...")
    log_info("Refreshing page")
    try:
        import pyautogui
        pyautogui.press('f5')
        time.sleep(0.5)
        # print("[WEB] ✅ Page refreshed")
        return True
    except Exception as e:
        # print(f"[WEB] Refresh failed: {e}")
        log_error(f"Refresh failed: {e}")
        return False


def go_to_url(url):
    """Navigate to specific URL"""
    # print(f"[WEB] Going to URL: {url}")
    log_info(f"Going to URL: {url}")
    try:
        import pyautogui

        # Add https if not present
        if not url.startswith('http'):
            url = 'https://' + url

        pyautogui.hotkey('ctrl', 'l')
        time.sleep(0.3)
        pyautogui.hotkey('ctrl', 'a')
        pyautogui.write(url, interval=0.03)
        pyautogui.press('enter')
        time.sleep(0.5)
        # print(f"[WEB] ✅ Navigated to: {url}")
        log_debug(f"Navigated to: {url}")
        return True
    except Exception as e:
        # print(f"[WEB] Go to URL failed: {e}")
        log_error(f"Go to URL failed: {e}")
        return False


# ── Bookmarks ─────────────────────────────────────────────────

def bookmark_page():
    """Bookmark current page"""
    # print("[WEB] Bookmarking page...")
    log_info("Bookmarking page")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'd')
        time.sleep(0.3)
        pyautogui.press('enter')  # Confirm bookmark
        # print("[WEB] ✅ Page bookmarked")
        return True
    except Exception as e:
        # print(f"[WEB] Bookmark failed: {e}")
        log_error(f"Bookmark failed: {e}")
        return False


# ── History ───────────────────────────────────────────────────

def open_history():
    """Open browser history"""
    # print("[WEB] Opening history...")
    log_info("Opening browser history")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'h')
        time.sleep(0.3)
        # print("[WEB] ✅ History opened")
        return True
    except Exception as e:
        # print(f"[WEB] Open history failed: {e}")
        log_error(f"Open history failed: {e}")
        return False


# ── Downloads ─────────────────────────────────────────────────

def open_downloads():
    """Open browser downloads"""
    # print("[WEB] Opening downloads...")
    log_info("Opening downloads")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'j')
        time.sleep(0.3)
        # print("[WEB] ✅ Downloads opened")
        return True
    except Exception as e:
        # print(f"[WEB] Open downloads failed: {e}")
        log_error(f"Open downloads failed: {e}")
        return False


# ── Zoom ──────────────────────────────────────────────────────

def zoom_in_browser():
    """Zoom in browser"""
    # print("[WEB] Zoom in browser...")
    log_info("Browser zoom in")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', '+')
        # print("[WEB] ✅ Browser zoomed in")
        return True
    except Exception as e:
        # print(f"[WEB] Browser zoom in failed: {e}")
        log_error(f"Browser zoom in failed: {e}")
        return False


def zoom_out_browser():
    """Zoom out browser"""
    # print("[WEB] Zoom out browser...")
    log_info("Browser zoom out")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', '-')
        # print("[WEB] ✅ Browser zoomed out")
        return True
    except Exception as e:
        # print(f"[WEB] Browser zoom out failed: {e}")
        log_error(f"Browser zoom out failed: {e}")
        return False


def reset_zoom_browser():
    """Reset browser zoom"""
    # print("[WEB] Reset browser zoom...")
    log_info("Browser zoom reset")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', '0')
        # print("[WEB] ✅ Browser zoom reset")
        return True
    except Exception as e:
        # print(f"[WEB] Browser zoom reset failed: {e}")
        log_error(f"Browser zoom reset failed: {e}")
        return False


# ── Find in Page ──────────────────────────────────────────────

def find_in_page(text):
    """Find text in current page"""
    # print(f"[WEB] Finding in page: {text}")
    log_info(f"Find in page: {text}")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'f')
        time.sleep(0.3)
        pyautogui.write(text, interval=0.05)
        # print(f"[WEB] ✅ Finding: {text}")
        return True
    except Exception as e:
        # print(f"[WEB] Find in page failed: {e}")
        log_error(f"Find in page failed: {e}")
        return False


# ── Incognito ─────────────────────────────────────────────────

def open_incognito():
    """Open incognito/private window"""
    # print("[WEB] Opening incognito...")
    log_info("Opening incognito window")
    try:
        import pyautogui
        # Works for Chrome/Edge (Ctrl+Shift+N)
        # Firefox uses Ctrl+Shift+P
        pyautogui.hotkey('ctrl', 'shift', 'n')
        time.sleep(0.5)
        # print("[WEB] ✅ Incognito opened")
        return True
    except Exception as e:
        # print(f"[WEB] Incognito failed: {e}")
        log_error(f"Incognito failed: {e}")
        return False


# ── Full Screen ───────────────────────────────────────────────

def toggle_fullscreen_browser():
    """Toggle browser fullscreen"""
    # print("[WEB] Toggle fullscreen...")
    log_info("Toggle browser fullscreen")
    try:
        import pyautogui
        pyautogui.press('f11')
        time.sleep(0.3)
        # print("[WEB] ✅ Fullscreen toggled")
        return True
    except Exception as e:
        # print(f"[WEB] Fullscreen failed: {e}")
        log_error(f"Toggle fullscreen failed: {e}")
        return False


# ── Developer Tools ───────────────────────────────────────────

def open_developer_tools():
    """Open browser developer tools"""
    # print("[WEB] Opening dev tools...")
    log_info("Opening developer tools")
    try:
        import pyautogui
        pyautogui.press('f12')
        time.sleep(0.3)
        # print("[WEB] ✅ Dev tools opened")
        return True
    except Exception as e:
        # print(f"[WEB] Dev tools failed: {e}")
        log_error(f"Dev tools failed: {e}")
        return False
    