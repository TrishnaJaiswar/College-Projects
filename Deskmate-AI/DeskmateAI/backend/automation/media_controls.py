# DeskmateAI/backend/automation/media_controls.py

import os
import sys
import time

# ============================================================
# MEDIA CONTROLS FOR DESKMATEAI
# Handles all media playback controls
# Play, Pause, Next, Previous, Stop
# Works with Spotify, VLC, YouTube, Windows Media
# Any media player that responds to media keys
# Three tier: pyautogui → pywinauto → ctypes
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Play / Pause ──────────────────────────────────────────────

def play_pause():
    """Toggle play/pause for any media player"""
    # print("[MEDIA] Play/Pause toggle...")
    log_info("Media play/pause toggle")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.press('playpause')
        # print("[MEDIA] ✅ Play/pause via media key")
        log_debug("Play/pause via media key")
        return True
    except Exception as e:
        # print(f"[MEDIA] Media key failed: {e}")
        log_warning(f"Media key play/pause failed: {e}")
        return _play_pause_via_space()


def _play_pause_via_space():
    """Fallback: use space bar for play/pause"""
    # print("[MEDIA] Fallback play/pause via space...")
    try:
        import pyautogui
        pyautogui.press('space')
        # print("[MEDIA] ✅ Play/pause via space")
        log_debug("Play/pause via space")
        return True
    except Exception as e:
        # print(f"[MEDIA] Space play/pause failed: {e}")
        log_error(f"Space play/pause failed: {e}")
        return False


def play():
    """Start media playback"""
    # print("[MEDIA] Play...")
    log_info("Media play")
    return play_pause()


def pause():
    """Pause media playback"""
    # print("[MEDIA] Pause...")
    log_info("Media pause")
    return play_pause()


# ── Next / Previous ───────────────────────────────────────────

def next_track():
    """Skip to next track"""
    # print("[MEDIA] Next track...")
    log_info("Next track")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.press('nexttrack')
        # print("[MEDIA] ✅ Next track via media key")
        log_debug("Next track via media key")
        return True
    except Exception as e:
        # print(f"[MEDIA] Next track media key failed: {e}")
        log_warning(f"Next track media key failed: {e}")
        return _next_via_shortcut()


def _next_via_shortcut():
    """Fallback next track via keyboard shortcut"""
    # print("[MEDIA] Fallback next via shortcut...")
    try:
        import pyautogui
        # Spotify shortcut
        pyautogui.hotkey('ctrl', 'right')
        # print("[MEDIA] ✅ Next via ctrl+right")
        log_debug("Next track via ctrl+right")
        return True
    except Exception as e:
        # print(f"[MEDIA] Next shortcut failed: {e}")
        log_error(f"Next track shortcut failed: {e}")
        return False


def previous_track():
    """Go to previous track"""
    # print("[MEDIA] Previous track...")
    log_info("Previous track")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.press('prevtrack')
        # print("[MEDIA] ✅ Previous track via media key")
        log_debug("Previous track via media key")
        return True
    except Exception as e:
        # print(f"[MEDIA] Previous track media key failed: {e}")
        log_warning(f"Previous track media key failed: {e}")
        return _previous_via_shortcut()


def _previous_via_shortcut():
    """Fallback previous track via keyboard shortcut"""
    # print("[MEDIA] Fallback previous via shortcut...")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'left')
        # print("[MEDIA] ✅ Previous via ctrl+left")
        log_debug("Previous track via ctrl+left")
        return True
    except Exception as e:
        # print(f"[MEDIA] Previous shortcut failed: {e}")
        log_error(f"Previous track shortcut failed: {e}")
        return False


# ── Stop ──────────────────────────────────────────────────────

def stop():
    """Stop media playback"""
    # print("[MEDIA] Stop...")
    log_info("Media stop")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.press('stop')
        # print("[MEDIA] ✅ Stop via media key")
        log_debug("Stop via media key")
        return True
    except Exception as e:
        # print(f"[MEDIA] Stop media key failed: {e}")
        log_warning(f"Stop media key failed: {e}")
        return False


# ── Spotify Specific ──────────────────────────────────────────

def spotify_play_pause():
    """Spotify specific play/pause"""
    # print("[MEDIA] Spotify play/pause...")
    log_info("Spotify play/pause")
    return _control_specific_player("spotify", play_pause)


def spotify_next():
    """Spotify next track"""
    # print("[MEDIA] Spotify next...")
    log_info("Spotify next")
    return _control_specific_player("spotify", next_track)


def spotify_previous():
    """Spotify previous track"""
    # print("[MEDIA] Spotify previous...")
    log_info("Spotify previous")
    return _control_specific_player("spotify", previous_track)


def spotify_like():
    """Like current Spotify song"""
    # print("[MEDIA] Spotify like...")
    log_info("Spotify like song")
    try:
        import pyautogui
        result = _focus_player("spotify")
        if result:
            pyautogui.hotkey('alt', 'shift', 'b')
            # print("[MEDIA] ✅ Spotify song liked")
            return True
        return False
    except Exception as e:
        # print(f"[MEDIA] Spotify like failed: {e}")
        log_error(f"Spotify like failed: {e}")
        return False


# ── VLC Specific ──────────────────────────────────────────────

def vlc_play_pause():
    """VLC specific play/pause"""
    # print("[MEDIA] VLC play/pause...")
    log_info("VLC play/pause")
    return _control_specific_player("vlc", play_pause)


def vlc_next():
    """VLC next"""
    # print("[MEDIA] VLC next...")
    log_info("VLC next")
    try:
        result = _focus_player("vlc")
        if result:
            import pyautogui
            pyautogui.hotkey('shift', 'n')
            # print("[MEDIA] ✅ VLC next")
            return True
        return next_track()
    except Exception as e:
        # print(f"[MEDIA] VLC next failed: {e}")
        log_error(f"VLC next failed: {e}")
        return False


def vlc_previous():
    """VLC previous"""
    # print("[MEDIA] VLC previous...")
    log_info("VLC previous")
    try:
        result = _focus_player("vlc")
        if result:
            import pyautogui
            pyautogui.hotkey('shift', 'p')
            # print("[MEDIA] ✅ VLC previous")
            return True
        return previous_track()
    except Exception as e:
        # print(f"[MEDIA] VLC previous failed: {e}")
        log_error(f"VLC previous failed: {e}")
        return False


def vlc_fullscreen():
    """VLC toggle fullscreen"""
    # print("[MEDIA] VLC fullscreen...")
    log_info("VLC fullscreen")
    try:
        result = _focus_player("vlc")
        if result:
            import pyautogui
            pyautogui.press('f')
            # print("[MEDIA] ✅ VLC fullscreen toggled")
            return True
        return False
    except Exception as e:
        # print(f"[MEDIA] VLC fullscreen failed: {e}")
        log_error(f"VLC fullscreen failed: {e}")
        return False


def vlc_subtitle_toggle():
    """VLC toggle subtitles"""
    # print("[MEDIA] VLC subtitle toggle...")
    log_info("VLC subtitle toggle")
    try:
        result = _focus_player("vlc")
        if result:
            import pyautogui
            pyautogui.press('v')
            # print("[MEDIA] ✅ VLC subtitles toggled")
            return True
        return False
    except Exception as e:
        # print(f"[MEDIA] VLC subtitle failed: {e}")
        log_error(f"VLC subtitle toggle failed: {e}")
        return False


# ── YouTube Specific ──────────────────────────────────────────

def youtube_play_pause():
    """YouTube play/pause"""
    # print("[MEDIA] YouTube play/pause...")
    log_info("YouTube play/pause")
    try:
        import pyautogui
        # Focus browser
        pyautogui.press('k')
        # print("[MEDIA] ✅ YouTube play/pause via K")
        return True
    except Exception as e:
        # print(f"[MEDIA] YouTube play/pause failed: {e}")
        log_error(f"YouTube play/pause failed: {e}")
        return False


def youtube_fullscreen():
    """YouTube toggle fullscreen"""
    # print("[MEDIA] YouTube fullscreen...")
    log_info("YouTube fullscreen")
    try:
        import pyautogui
        pyautogui.press('f')
        # print("[MEDIA] ✅ YouTube fullscreen toggled")
        return True
    except Exception as e:
        # print(f"[MEDIA] YouTube fullscreen failed: {e}")
        log_error(f"YouTube fullscreen failed: {e}")
        return False


def youtube_mute():
    """YouTube mute/unmute"""
    # print("[MEDIA] YouTube mute...")
    log_info("YouTube mute")
    try:
        import pyautogui
        pyautogui.press('m')
        # print("[MEDIA] ✅ YouTube mute toggled")
        return True
    except Exception as e:
        # print(f"[MEDIA] YouTube mute failed: {e}")
        log_error(f"YouTube mute failed: {e}")
        return False


def youtube_skip_forward():
    """YouTube skip forward 5 seconds"""
    # print("[MEDIA] YouTube skip forward...")
    log_info("YouTube skip forward")
    try:
        import pyautogui
        pyautogui.press('l')
        # print("[MEDIA] ✅ YouTube skipped forward 10s")
        return True
    except Exception as e:
        # print(f"[MEDIA] YouTube skip failed: {e}")
        log_error(f"YouTube skip forward failed: {e}")
        return False


def youtube_skip_backward():
    """YouTube skip backward 5 seconds"""
    # print("[MEDIA] YouTube skip backward...")
    log_info("YouTube skip backward")
    try:
        import pyautogui
        pyautogui.press('j')
        # print("[MEDIA] ✅ YouTube skipped backward 10s")
        return True
    except Exception as e:
        # print(f"[MEDIA] YouTube skip backward failed: {e}")
        log_error(f"YouTube skip backward failed: {e}")
        return False


def youtube_subtitle_toggle():
    """YouTube toggle subtitles"""
    # print("[MEDIA] YouTube subtitle toggle...")
    log_info("YouTube subtitle toggle")
    try:
        import pyautogui
        pyautogui.press('c')
        # print("[MEDIA] ✅ YouTube subtitles toggled")
        return True
    except Exception as e:
        # print(f"[MEDIA] YouTube subtitle failed: {e}")
        log_error(f"YouTube subtitle toggle failed: {e}")
        return False


# ── Seek ──────────────────────────────────────────────────────

def seek_forward(seconds=10):
    """Seek forward in media"""
    # print(f"[MEDIA] Seek forward: {seconds}s")
    log_info(f"Seek forward {seconds}s")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'right')
        # print(f"[MEDIA] ✅ Seeked forward")
        return True
    except Exception as e:
        # print(f"[MEDIA] Seek forward failed: {e}")
        log_error(f"Seek forward failed: {e}")
        return False


def seek_backward(seconds=10):
    """Seek backward in media"""
    # print(f"[MEDIA] Seek backward: {seconds}s")
    log_info(f"Seek backward {seconds}s")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'left')
        # print(f"[MEDIA] ✅ Seeked backward")
        return True
    except Exception as e:
        # print(f"[MEDIA] Seek backward failed: {e}")
        log_error(f"Seek backward failed: {e}")
        return False


# ── Helper Functions ──────────────────────────────────────────

def _focus_player(player_name):
    """Focus specific media player window"""
    # print(f"[MEDIA] Focusing player: {player_name}")
    try:
        import win32gui

        found_hwnd = None

        def callback(hwnd, _):
            nonlocal found_hwnd
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                if player_name.lower() in title:
                    found_hwnd = hwnd

        win32gui.EnumWindows(callback, None)

        if found_hwnd:
            win32gui.SetForegroundWindow(found_hwnd)
            time.sleep(0.3)
            # print(f"[MEDIA] ✅ Focused: {player_name}")
            log_debug(f"Focused player: {player_name}")
            return True

        # print(f"[MEDIA] Player not found: {player_name}")
        log_warning(f"Player not found: {player_name}")
        return False

    except Exception as e:
        # print(f"[MEDIA] Focus player failed: {e}")
        log_error(f"Focus player failed: {e}")
        return False


def _control_specific_player(player_name, control_fn):
    """Focus player then execute control"""
    # print(f"[MEDIA] Controlling {player_name}...")
    focused = _focus_player(player_name)
    if focused:
        return control_fn()
    else:
        # Fallback to generic media key
        # print(f"[MEDIA] Player not focused, using generic control")
        return control_fn()


def get_active_media_player():
    """Detect which media player is currently active"""
    # print("[MEDIA] Detecting active media player...")
    try:
        import win32gui

        media_players = [
            'spotify', 'vlc', 'youtube', 'netflix',
            'windows media', 'groove', 'itunes',
            'winamp', 'foobar', 'musicbee'
        ]

        found = []

        def callback(hwnd, _):
            if win32gui.IsWindowVisible(hwnd):
                title = win32gui.GetWindowText(hwnd).lower()
                for player in media_players:
                    if player in title:
                        found.append(player)

        win32gui.EnumWindows(callback, None)
        # print(f"[MEDIA] Active media players: {found}")
        return found[0] if found else None

    except Exception as e:
        # print(f"[MEDIA] Detect player failed: {e}")
        log_error(f"Detect media player failed: {e}")
        return None