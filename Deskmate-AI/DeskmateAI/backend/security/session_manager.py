# DeskmateAI/backend/security/session_manager.py

import os
import sys
import time

# ============================================================
# SESSION MANAGER FOR DESKMATEAI
# Manages user sessions after successful login
# Tracks:
# - Current logged in user
# - Session start time
# - Session token
# - Authentication method used
# - Session expiry
# Sessions persist in memory only (not saved to disk)
# On app restart, user must login again
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import (
    load_profile,
    save_profile,
    get_timestamp,
    list_users
)

# ── Session Class ─────────────────────────────────────────────

class Session:
    def __init__(self, username, profile, auth_method):
        self.username = username
        self.profile = profile
        self.auth_method = auth_method
        self.start_time = time.time()
        self.last_activity = time.time()
        self.is_active = True
        self.language = profile.get('language', 'en')
        self.language_name = profile.get('language_name', 'English')
        self.wake_word = profile.get('wake_word', 'hey deskmate')
        self.wake_word_sensitivity = profile.get('wake_word_sensitivity', 0.6)
        self.is_admin = profile.get('is_admin', False)

        # print(f"[SESSION] Created session: {username} via {auth_method}")
        log_info(f"Session created: {username} via {auth_method}")

    def update_activity(self):
        """Update last activity timestamp"""
        self.last_activity = time.time()

    def get_duration(self):
        """Get session duration in seconds"""
        return time.time() - self.start_time

    def get_idle_time(self):
        """Get idle time in seconds"""
        return time.time() - self.last_activity

    def to_dict(self):
        """Convert session to dictionary"""
        return {
            "username": self.username,
            "auth_method": self.auth_method,
            "start_time": self.start_time,
            "last_activity": self.last_activity,
            "is_active": self.is_active,
            "language": self.language,
            "language_name": self.language_name,
            "wake_word": self.wake_word,
            "is_admin": self.is_admin,
            "duration_seconds": self.get_duration()
        }


# ── Session Manager Class ─────────────────────────────────────

class SessionManager:

    def __init__(self):
        # print("[SESSION_MGR] Initializing SessionManager...")
        self._current_session = None
        self._session_history = []
        log_info("SessionManager initialized")

    # ── Create Session ────────────────────────────────────────

    def create_session(self, username, auth_method):
        """
        Create new session after successful login
        Loads full user profile
        Updates last login timestamp
        Returns session object
        """
        # print(f"[SESSION_MGR] Creating session: {username}")
        log_info(f"Creating session: {username}")

        try:
            # Load profile
            profile = load_profile(username)
            if not profile:
                # print(f"[SESSION_MGR] Profile not found: {username}")
                log_error(f"Profile not found: {username}")
                return None

            # Create session
            session = Session(username, profile, auth_method)
            self._current_session = session

            # Update last login in profile
            profile['last_login'] = get_timestamp()
            save_profile(username, profile)

            # Add to history
            self._session_history.append({
                "username": username,
                "auth_method": auth_method,
                "login_time": get_timestamp()
            })

            # print(f"[SESSION_MGR] ✅ Session created: {username}")
            log_info(f"Session active: {username}")
            return session

        except Exception as e:
            # print(f"[SESSION_MGR] Session creation error: {e}")
            log_error(f"Session creation error: {e}")
            return None

    # ── Get Current Session ───────────────────────────────────

    def get_current_session(self):
        """Get currently active session"""
        # print(f"[SESSION_MGR] Getting current session...")
        if self._current_session and self._current_session.is_active:
            self._current_session.update_activity()
            return self._current_session
        return None

    def get_current_user(self):
        """Get current logged in username"""
        session = self.get_current_session()
        if session:
            return session.username
        return None

    def get_current_profile(self):
        """Get current user profile"""
        # print("[SESSION_MGR] Getting current profile...")
        username = self.get_current_user()
        if username:
            return load_profile(username)
        return None

    def get_current_language(self):
        """Get current user language"""
        session = self.get_current_session()
        if session:
            return session.language
        return 'en'

    def get_current_wake_word(self):
        """Get current user wake word"""
        session = self.get_current_session()
        if session:
            return session.wake_word
        return 'hey deskmate'

    def is_admin(self):
        """Check if current user is admin"""
        session = self.get_current_session()
        if session:
            return session.is_admin
        return False

    # ── Session State ─────────────────────────────────────────

    def is_logged_in(self):
        """Check if user is currently logged in"""
        result = (
            self._current_session is not None and
            self._current_session.is_active
        )
        # print(f"[SESSION_MGR] Is logged in: {result}")
        return result

    def update_activity(self):
        """Update session activity timestamp"""
        if self._current_session:
            self._current_session.update_activity()

    # ── End Session ───────────────────────────────────────────

    def end_session(self):
        """End current session (logout)"""
        # print("[SESSION_MGR] Ending session...")
        if self._current_session:
            username = self._current_session.username
            duration = self._current_session.get_duration()
            self._current_session.is_active = False

            # Update session history
            if self._session_history:
                self._session_history[-1]['logout_time'] = get_timestamp()
                self._session_history[-1]['duration_seconds'] = duration

            self._current_session = None
            log_info(f"Session ended: {username} | Duration: {duration:.1f}s")
            # print(f"[SESSION_MGR] ✅ Session ended: {username}")
            return True
        return False

    # ── Update Session Settings ───────────────────────────────

    def update_language(self, language_code, language_name):
        """Update language in current session"""
        # print(f"[SESSION_MGR] Updating language: {language_code}")
        if self._current_session:
            self._current_session.language = language_code
            self._current_session.language_name = language_name
            log_info(f"Session language updated: {language_code}")
            return True
        return False

    def update_wake_word(self, wake_word, sensitivity=0.6):
        """Update wake word in current session"""
        # print(f"[SESSION_MGR] Updating wake word: {wake_word}")
        if self._current_session:
            self._current_session.wake_word = wake_word.lower().strip()
            self._current_session.wake_word_sensitivity = sensitivity
            log_info(f"Session wake word updated: {wake_word}")
            return True
        return False

    def refresh_profile(self):
        """Reload profile from disk into session"""
        # print("[SESSION_MGR] Refreshing profile...")
        if self._current_session:
            username = self._current_session.username
            profile = load_profile(username)
            if profile:
                self._current_session.profile = profile
                self._current_session.language = profile.get('language', 'en')
                self._current_session.language_name = profile.get('language_name', 'English')
                self._current_session.wake_word = profile.get('wake_word', 'hey deskmate')
                self._current_session.wake_word_sensitivity = profile.get('wake_word_sensitivity', 0.6)
                self._current_session.is_admin = profile.get('is_admin', False)
                # print(f"[SESSION_MGR] ✅ Profile refreshed: {username}")
                log_debug(f"Session profile refreshed: {username}")
                return True
        return False

    # ── Session Info ──────────────────────────────────────────

    def get_session_info(self):
        """Get current session information"""
        # print("[SESSION_MGR] Getting session info...")
        if not self._current_session:
            return None
        return self._current_session.to_dict()

    def get_session_history(self):
        """Get session history"""
        return self._session_history

    # ── Available Users ───────────────────────────────────────

    def get_available_users(self):
        """
        Get list of users available for login
        Returns list of user info dicts
        """
        # print("[SESSION_MGR] Getting available users...")
        try:
            users = list_users()
            available = []

            for username in users:
                profile = load_profile(username)
                if profile and profile.get('registration_complete', False):
                    available.append({
                        "username": username,
                        "is_admin": profile.get('is_admin', False),
                        "language": profile.get('language', 'en'),
                        "language_name": profile.get('language_name', 'English'),
                        "last_login": profile.get('last_login'),
                        "auth_methods": profile.get('auth_methods', []),
                        "face_samples": profile.get('face_samples', 0),
                        "speaker_samples": profile.get('speaker_samples', 0)
                    })

            # print(f"[SESSION_MGR] Available users: {len(available)}")
            log_debug(f"Available users: {len(available)}")
            return available

        except Exception as e:
            # print(f"[SESSION_MGR] Get users error: {e}")
            log_error(f"Get available users error: {e}")
            return []

    def get_incomplete_registrations(self):
        """Get users with incomplete registration"""
        # print("[SESSION_MGR] Getting incomplete registrations...")
        try:
            users = list_users()
            incomplete = []

            for username in users:
                profile = load_profile(username)
                if profile and not profile.get('registration_complete', False):
                    incomplete.append(username)

            # print(f"[SESSION_MGR] Incomplete: {incomplete}")
            return incomplete

        except Exception as e:
            # print(f"[SESSION_MGR] Incomplete reg error: {e}")
            log_error(f"Get incomplete registrations error: {e}")
            return []


# ── Singleton Instance ────────────────────────────────────────

_session_manager = None

def get_session_manager():
    global _session_manager
    if _session_manager is None:
        # print("[SESSION_MGR] Creating singleton SessionManager...")
        _session_manager = SessionManager()
    return _session_manager

'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `Session` class | Stores all session data |
| `create_session()` | Creates session after login |
| `get_current_session()` | Returns active session |
| `get_current_user()` | Returns logged in username |
| `get_current_language()` | Returns user language |
| `get_current_wake_word()` | Returns user wake word |
| `is_admin()` | Check admin status |
| `is_logged_in()` | Check if user logged in |
| `end_session()` | Logout user |
| `update_language()` | Update language in session |
| `update_wake_word()` | Update wake word in session |
| `refresh_profile()` | Reload profile from disk |
| `get_session_info()` | Full session details |
| `get_available_users()` | List users for login screen |
| `get_incomplete_registrations()` | Find incomplete setups |
| `get_session_manager()` | Singleton — creates once |

---

## How sessions work:
```
Login successful
        ↓
create_session() called
        ↓
Session object created in RAM
        ↓
last_login updated in profile.json ✅
        ↓
All pipeline operations use session
        ↓
User logs out
        ↓
end_session() called
        ↓
Session cleared from RAM
        ↓
App restart = must login again ✅
'''