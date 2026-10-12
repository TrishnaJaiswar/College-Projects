# DeskmateAI/backend/automation/system_controls.py

import os
import sys
import time
import ctypes

# ============================================================
# SYSTEM CONTROLS FOR DESKMATEAI
# Handles all system level operations
# Volume, Brightness, Shutdown, Restart, Sleep, Lock
# Three tier: pyautogui → screen_brightness_control → ctypes
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Volume Control ────────────────────────────────────────────

# Steps for volume change
VOLUME_STEPS = 5

def volume_up(steps=None):
    """Increase system volume"""
    # print(f"[SYSTEM] Volume up: {steps or VOLUME_STEPS} steps")
    log_info(f"Volume up: {steps or VOLUME_STEPS} steps")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        presses = steps if steps else VOLUME_STEPS
        pyautogui.press('volumeup', presses=presses, interval=0.05)
        # print(f"[SYSTEM] ✅ Volume increased by {presses} steps")
        log_debug(f"Volume increased by {presses} steps")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Volume up failed: {e}")
        log_error(f"Volume up failed: {e}")
        return _volume_up_ctypes(steps or VOLUME_STEPS)


def volume_down(steps=None):
    """Decrease system volume"""
    # print(f"[SYSTEM] Volume down: {steps or VOLUME_STEPS} steps")
    log_info(f"Volume down: {steps or VOLUME_STEPS} steps")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        presses = steps if steps else VOLUME_STEPS
        pyautogui.press('volumedown', presses=presses, interval=0.05)
        # print(f"[SYSTEM] ✅ Volume decreased by {presses} steps")
        log_debug(f"Volume decreased by {presses} steps")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Volume down failed: {e}")
        log_error(f"Volume down failed: {e}")
        return _volume_down_ctypes(steps or VOLUME_STEPS)


def mute():
    """Mute system audio"""
    # print("[SYSTEM] Muting audio...")
    log_info("Muting audio")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.press('volumemute')
        # print("[SYSTEM] ✅ Audio muted")
        log_debug("Audio muted")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Mute failed: {e}")
        log_error(f"Mute failed: {e}")
        return _mute_ctypes()


def unmute():
    """Unmute system audio"""
    # print("[SYSTEM] Unmuting audio...")
    log_info("Unmuting audio")
    try:
        import pyautogui
        pyautogui.FAILSAFE = False
        pyautogui.press('volumemute')
        # print("[SYSTEM] ✅ Audio unmuted")
        log_debug("Audio unmuted")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Unmute failed: {e}")
        log_error(f"Unmute failed: {e}")
        return _mute_ctypes()


def set_volume(level):
    """Set volume to specific level 0-100"""
    # print(f"[SYSTEM] Setting volume to: {level}%")
    log_info(f"Setting volume to: {level}%")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))

        # Convert 0-100 to 0.0-1.0
        volume_scalar = level / 100.0
        volume.SetMasterVolumeLevelScalar(volume_scalar, None)
        # print(f"[SYSTEM] ✅ Volume set to {level}%")
        log_debug(f"Volume set to {level}%")
        return True

    except Exception as e:
        # print(f"[SYSTEM] Set volume failed: {e}")
        log_warning(f"pycaw set volume failed: {e}")
        # Fallback - press volume keys to approximate
        return _approximate_volume(level)


def get_volume():
    """Get current volume level"""
    # print("[SYSTEM] Getting current volume...")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        level = int(current * 100)
        # print(f"[SYSTEM] Current volume: {level}%")
        return level
    except Exception as e:
        # print(f"[SYSTEM] Get volume failed: {e}")
        log_error(f"Get volume failed: {e}")
        return None


def _volume_up_ctypes(steps):
    """Fallback volume up via ctypes"""
    # print(f"[SYSTEM] ctypes volume up: {steps}")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        new_level = min(1.0, current + (steps * 0.02))
        volume.SetMasterVolumeLevelScalar(new_level, None)
        # print(f"[SYSTEM] ✅ ctypes volume up to {new_level:.2f}")
        return True
    except Exception as e:
        # print(f"[SYSTEM] ctypes volume up failed: {e}")
        log_error(f"ctypes volume up failed: {e}")
        return False


def _volume_down_ctypes(steps):
    """Fallback volume down via ctypes"""
    # print(f"[SYSTEM] ctypes volume down: {steps}")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        current = volume.GetMasterVolumeLevelScalar()
        new_level = max(0.0, current - (steps * 0.02))
        volume.SetMasterVolumeLevelScalar(new_level, None)
        # print(f"[SYSTEM] ✅ ctypes volume down to {new_level:.2f}")
        return True
    except Exception as e:
        # print(f"[SYSTEM] ctypes volume down failed: {e}")
        log_error(f"ctypes volume down failed: {e}")
        return False


def _mute_ctypes():
    """Fallback mute via ctypes"""
    # print("[SYSTEM] ctypes mute...")
    try:
        from ctypes import cast, POINTER
        from comtypes import CLSCTX_ALL
        from pycaw.pycaw import AudioUtilities, IAudioEndpointVolume

        devices = AudioUtilities.GetSpeakers()
        interface = devices.Activate(
            IAudioEndpointVolume._iid_,
            CLSCTX_ALL,
            None
        )
        volume = cast(interface, POINTER(IAudioEndpointVolume))
        is_muted = volume.GetMute()
        volume.SetMute(not is_muted, None)
        # print(f"[SYSTEM] ✅ ctypes mute toggled: {not is_muted}")
        return True
    except Exception as e:
        # print(f"[SYSTEM] ctypes mute failed: {e}")
        log_error(f"ctypes mute failed: {e}")
        return False


def _approximate_volume(target_level):
    """Approximate volume by pressing keys"""
    # print(f"[SYSTEM] Approximating volume to {target_level}%")
    try:
        import pyautogui
        # First mute then set
        # Press volume down 50 times to go to 0
        pyautogui.press('volumedown', presses=50, interval=0.01)
        # Then press up to target
        presses = target_level // 2
        pyautogui.press('volumeup', presses=presses, interval=0.01)
        # print(f"[SYSTEM] ✅ Approximated volume to ~{target_level}%")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Approximate volume failed: {e}")
        log_error(f"Approximate volume failed: {e}")
        return False


# ── Brightness Control ────────────────────────────────────────

BRIGHTNESS_STEPS = 10

def brightness_up(steps=None):
    """Increase screen brightness"""
    # print(f"[SYSTEM] Brightness up: {steps or BRIGHTNESS_STEPS} steps")
    log_info(f"Brightness up: {steps or BRIGHTNESS_STEPS} steps")
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)
        if isinstance(current, list):
            current = current[0]
        new_brightness = min(100, current + (steps or BRIGHTNESS_STEPS))
        sbc.set_brightness(new_brightness, display=0)
        # print(f"[SYSTEM] ✅ Brightness increased to {new_brightness}%")
        log_debug(f"Brightness increased to {new_brightness}%")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Brightness up failed: {e}")
        log_error(f"Brightness up failed: {e}")
        return False


def brightness_down(steps=None):
    """Decrease screen brightness"""
    # print(f"[SYSTEM] Brightness down: {steps or BRIGHTNESS_STEPS} steps")
    log_info(f"Brightness down: {steps or BRIGHTNESS_STEPS} steps")
    try:
        import screen_brightness_control as sbc
        current = sbc.get_brightness(display=0)
        if isinstance(current, list):
            current = current[0]
        new_brightness = max(10, current - (steps or BRIGHTNESS_STEPS))
        sbc.set_brightness(new_brightness, display=0)
        # print(f"[SYSTEM] ✅ Brightness decreased to {new_brightness}%")
        log_debug(f"Brightness decreased to {new_brightness}%")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Brightness down failed: {e}")
        log_error(f"Brightness down failed: {e}")
        return False


def set_brightness(level):
    """Set brightness to specific level 0-100"""
    # print(f"[SYSTEM] Setting brightness to: {level}%")
    log_info(f"Setting brightness to: {level}%")
    try:
        import screen_brightness_control as sbc
        level = max(10, min(100, level))
        sbc.set_brightness(level, display=0)
        # print(f"[SYSTEM] ✅ Brightness set to {level}%")
        log_debug(f"Brightness set to {level}%")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Set brightness failed: {e}")
        log_error(f"Set brightness failed: {e}")
        return False


def get_brightness():
    """Get current brightness level"""
    # print("[SYSTEM] Getting current brightness...")
    try:
        import screen_brightness_control as sbc
        brightness = sbc.get_brightness(display=0)
        if isinstance(brightness, list):
            brightness = brightness[0]
        # print(f"[SYSTEM] Current brightness: {brightness}%")
        return brightness
    except Exception as e:
        # print(f"[SYSTEM] Get brightness failed: {e}")
        log_error(f"Get brightness failed: {e}")
        return None


# ── System Power ──────────────────────────────────────────────

def shutdown():
    """Shutdown the system"""
    # print("[SYSTEM] Initiating shutdown...")
    log_info("System shutdown initiated")
    try:
        # Layer 1: os.system
        os.system("shutdown /s /t 5")
        # print("[SYSTEM] ✅ Shutdown command sent")
        log_info("Shutdown command sent (5 second delay)")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Shutdown Layer 1 failed: {e}")
        log_warning(f"os.system shutdown failed: {e}")
        try:
            # Layer 2: ctypes
            ctypes.windll.advapi32.InitiateSystemShutdownExW(
                None, None, 5, True, False, 0
            )
            # print("[SYSTEM] ✅ ctypes shutdown sent")
            return True
        except Exception as e2:
            # print(f"[SYSTEM] Shutdown Layer 2 failed: {e2}")
            log_error(f"ctypes shutdown failed: {e2}")
            return False


def restart():
    """Restart the system"""
    # print("[SYSTEM] Initiating restart...")
    log_info("System restart initiated")
    try:
        os.system("shutdown /r /t 5")
        # print("[SYSTEM] ✅ Restart command sent")
        log_info("Restart command sent (5 second delay)")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Restart failed: {e}")
        log_error(f"Restart failed: {e}")
        return False


def cancel_shutdown():
    """Cancel pending shutdown"""
    # print("[SYSTEM] Cancelling shutdown...")
    log_info("Cancelling shutdown")
    try:
        os.system("shutdown /a")
        # print("[SYSTEM] ✅ Shutdown cancelled")
        log_info("Shutdown cancelled")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Cancel shutdown failed: {e}")
        log_error(f"Cancel shutdown failed: {e}")
        return False


def sleep():
    """Put system to sleep"""
    # print("[SYSTEM] Going to sleep...")
    log_info("System sleep initiated")
    try:
        # Layer 1: pyautogui
        import pyautogui
        # Press Win key
        pyautogui.press('win')
        time.sleep(0.5)
        # Type sleep
        pyautogui.write('sleep', interval=0.05)
        time.sleep(0.5)
        pyautogui.press('enter')
        time.sleep(0.3)
        # print("[SYSTEM] ✅ Sleep command via pyautogui")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Sleep Layer 1 failed: {e}")
        log_warning(f"pyautogui sleep failed: {e}")
        try:
            # Layer 2: ctypes
            ctypes.windll.PowrProf.SetSuspendState(0, 1, 0)
            # print("[SYSTEM] ✅ Sleep via ctypes")
            log_info("Sleep via ctypes")
            return True
        except Exception as e2:
            # print(f"[SYSTEM] Sleep Layer 2 failed: {e2}")
            log_error(f"ctypes sleep failed: {e2}")
            return False


def hibernate():
    """Hibernate the system"""
    # print("[SYSTEM] Hibernating...")
    log_info("System hibernate initiated")
    try:
        ctypes.windll.PowrProf.SetSuspendState(1, 1, 0)
        # print("[SYSTEM] ✅ Hibernate initiated")
        log_info("Hibernate initiated")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Hibernate failed: {e}")
        log_error(f"Hibernate failed: {e}")
        return False


def lock_screen():
    """Lock the screen"""
    # print("[SYSTEM] Locking screen...")
    log_info("Locking screen")
    try:
        # Layer 1: pyautogui
        import pyautogui
        pyautogui.hotkey('win', 'l')
        # print("[SYSTEM] ✅ Screen locked via pyautogui")
        log_debug("Screen locked via Win+L")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Lock Layer 1 failed: {e}")
        log_warning(f"pyautogui lock failed: {e}")
        try:
            # Layer 2: ctypes
            ctypes.windll.user32.LockWorkStation()
            # print("[SYSTEM] ✅ Screen locked via ctypes")
            log_info("Screen locked via ctypes")
            return True
        except Exception as e2:
            # print(f"[SYSTEM] Lock Layer 2 failed: {e2}")
            log_error(f"ctypes lock failed: {e2}")
            return False


def sign_out():
    """Sign out current user"""
    # print("[SYSTEM] Signing out...")
    log_info("Sign out initiated")
    try:
        os.system("shutdown /l")
        # print("[SYSTEM] ✅ Sign out command sent")
        log_info("Sign out command sent")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Sign out failed: {e}")
        log_error(f"Sign out failed: {e}")
        return False


# ── Clipboard ─────────────────────────────────────────────────

def get_clipboard():
    """Get clipboard content"""
    # print("[SYSTEM] Getting clipboard...")
    try:
        import pyperclip
        content = pyperclip.paste()
        # print(f"[SYSTEM] Clipboard: {content[:50]}...")
        return content
    except Exception as e:
        # print(f"[SYSTEM] Get clipboard failed: {e}")
        log_error(f"Get clipboard failed: {e}")
        return None


def set_clipboard(text):
    """Set clipboard content"""
    # print(f"[SYSTEM] Setting clipboard: {text[:50]}...")
    try:
        import pyperclip
        pyperclip.copy(text)
        # print("[SYSTEM] ✅ Clipboard set")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Set clipboard failed: {e}")
        log_error(f"Set clipboard failed: {e}")
        return False


# ── Task Manager ──────────────────────────────────────────────

def open_task_manager():
    """Open Task Manager"""
    # print("[SYSTEM] Opening Task Manager...")
    log_info("Opening Task Manager")
    try:
        import pyautogui
        pyautogui.hotkey('ctrl', 'shift', 'esc')
        time.sleep(0.5)
        # print("[SYSTEM] ✅ Task Manager opened")
        return True
    except Exception as e:
        # print(f"[SYSTEM] Task Manager failed: {e}")
        log_error(f"Task Manager failed: {e}")
        return False


# ── Screenshot ────────────────────────────────────────────────

def take_screenshot():
    """Take screenshot and save to Desktop"""
    # print("[SYSTEM] Taking screenshot...")
    log_info("Taking screenshot")
    try:
        import pyautogui
        from datetime import datetime

        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        desktop = os.path.join(os.path.expanduser("~"), "Desktop")
        filename = os.path.join(desktop, f"screenshot_{timestamp}.png")

        screenshot = pyautogui.screenshot()
        screenshot.save(filename)

        # print(f"[SYSTEM] ✅ Screenshot saved: {filename}")
        log_info(f"Screenshot saved: {filename}")
        return True

    except Exception as e:
        # print(f"[SYSTEM] Screenshot failed: {e}")
        log_error(f"Screenshot failed: {e}")
        return False


# ── System Info ───────────────────────────────────────────────

def get_battery_status():
    """Get battery status"""
    # print("[SYSTEM] Getting battery status...")
    try:
        import psutil
        battery = psutil.sensors_battery()
        if battery:
            status = {
                "percent": battery.percent,
                "plugged": battery.power_plugged,
                "time_left": battery.secsleft
            }
            # print(f"[SYSTEM] Battery: {status}")
            return status
        return None
    except Exception as e:
        # print(f"[SYSTEM] Battery status failed: {e}")
        log_error(f"Battery status failed: {e}")
        return None


def get_system_info():
    """Get basic system information"""
    # print("[SYSTEM] Getting system info...")
    try:
        import psutil
        info = {
            "cpu_percent": psutil.cpu_percent(interval=1),
            "memory_percent": psutil.virtual_memory().percent,
            "disk_percent": psutil.disk_usage('/').percent,
        }
        # print(f"[SYSTEM] System info: {info}")
        return info
    except Exception as e:
        # print(f"[SYSTEM] System info failed: {e}")
        log_error(f"System info failed: {e}")
        return {}