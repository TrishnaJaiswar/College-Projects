# DeskmateAI/backend/security/auth_orchestrator.py

import os
import sys

# ============================================================
# AUTH ORCHESTRATOR FOR DESKMATEAI
# Central authentication coordinator
# Manages:
# - Login flow (password/voice/face)
# - Registration coordination
# - Admin authorization
# - Session management
# - Per-command speaker verification
# Single entry point for all auth operations
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.security.password_auth import get_password_auth
from backend.security.face_auth import get_face_auth
from backend.security.speech_auth import get_speech_auth
from backend.security.registration import get_registration_manager
from backend.security.session_manager import get_session_manager
from backend.utils.logger import log_info, log_error, log_debug, log_warning, log_auth

# ── Auth Orchestrator Class ───────────────────────────────────

class AuthOrchestrator:

    def __init__(self):
        # print("[AUTH] Initializing AuthOrchestrator...")
        self.password_auth = get_password_auth()
        self.face_auth = get_face_auth()
        self._speech_auth = None  # Lazy load
        self.registration = get_registration_manager()
        self.session = get_session_manager()
        log_info("AuthOrchestrator initialized")

    @property
    def speech_auth(self):
        """Lazy load speech auth to prevent blocking Qt event loop"""
        if self._speech_auth is None:
            # print("[AUTH] Lazy loading SpeechAuth...")
            self._speech_auth = get_speech_auth()
        return self._speech_auth

    # ── System State ──────────────────────────────────────────

    def is_first_run(self):
        """Check if system has no users registered"""
        result = self.registration.is_first_run()
        # print(f"[AUTH] Is first run: {result}")
        return result

    def is_logged_in(self):
        """Check if user is currently logged in"""
        return self.session.is_logged_in()

    def get_current_user(self):
        """Get currently logged in user"""
        return self.session.get_current_user()

    def get_current_profile(self):
        """Get current user profile"""
        return self.session.get_current_profile()

    def get_available_users(self):
        """Get list of users available to login"""
        return self.session.get_available_users()

    # ── Login ─────────────────────────────────────────────────

    def login_with_password(self, username, password):
        """
        Login with username and password
        Returns (success, message, profile)
        """
        # print(f"[AUTH] Password login: {username}")
        log_info(f"Password login attempt: {username}")

        try:
            # Authenticate
            success, message = self.password_auth.authenticate(
                username, password
            )

            if success:
                # Create session
                session = self.session.create_session(username, 'password')
                if session:
                    profile = session.profile
                    log_auth(username, 'password', True)
                    # print(f"[AUTH] ✅ Password login successful: {username}")
                    return True, "Login successful", profile
                else:
                    return False, "Failed to create session", None
            else:
                log_auth(username, 'password', False)
                # print(f"[AUTH] ❌ Password login failed: {username}")
                return False, message, None

        except Exception as e:
            # print(f"[AUTH] Password login error: {e}")
            log_error(f"Password login error: {e}")
            return False, str(e), None

    def login_with_face(self, username, progress_callback=None):
        """
        Login with face recognition
        Returns (success, message, profile)
        """
        # print(f"[AUTH] Face login: {username}")
        log_info(f"Face login attempt: {username}")

        try:
            # Check face registered
            if not self.face_auth.is_registered(username):
                # print(f"[AUTH] Face not registered: {username}")
                return False, "Face authentication not set up", None

            # Verify face
            success = self.face_auth.verify(
                username,
                progress_callback=progress_callback
            )

            if success:
                session = self.session.create_session(username, 'face')
                if session:
                    profile = session.profile
                    log_auth(username, 'face', True)
                    # print(f"[AUTH] ✅ Face login successful: {username}")
                    return True, "Face authentication successful", profile
                else:
                    return False, "Failed to create session", None
            else:
                log_auth(username, 'face', False)
                # print(f"[AUTH] ❌ Face login failed: {username}")
                return False, "Face not recognized", None

        except Exception as e:
            # print(f"[AUTH] Face login error: {e}")
            log_error(f"Face login error: {e}")
            return False, str(e), None

    def login_with_voice(self, username):
        """
        Login with voice password
        Returns (success, message, profile)
        """
        # print(f"[AUTH] Voice login: {username}")
        log_info(f"Voice login attempt: {username}")

        try:
            # Check voice password registered
            if not self.speech_auth.is_voice_password_registered(username):
                # print(f"[AUTH] Voice password not registered: {username}")
                return False, "Voice password not set up", None

            # Verify voice password
            success, message = self.speech_auth.login_with_voice_password(
                username
            )

            if success:
                session = self.session.create_session(username, 'voice')
                if session:
                    profile = session.profile
                    log_auth(username, 'voice', True)
                    # print(f"[AUTH] ✅ Voice login successful: {username}")
                    return True, "Voice authentication successful", profile
                else:
                    return False, "Failed to create session", None
            else:
                log_auth(username, 'voice', False)
                # print(f"[AUTH] ❌ Voice login failed: {message}")
                return False, message, None

        except Exception as e:
            # print(f"[AUTH] Voice login error: {e}")
            log_error(f"Voice login error: {e}")
            return False, str(e), None

    def login(self, username, auth_method, credential=None,
              progress_callback=None):
        """
        Universal login method
        Routes to correct auth method
        Returns (success, message, profile)
        """
        # print(f"[AUTH] Login: {username} via {auth_method}")
        log_info(f"Login attempt: {username} via {auth_method}")

        if auth_method == 'password':
            return self.login_with_password(username, credential)
        elif auth_method == 'face':
            return self.login_with_face(username, progress_callback)
        elif auth_method == 'voice':
            return self.login_with_voice(username)
        else:
            return False, f"Unknown auth method: {auth_method}", None

    # ── Logout ────────────────────────────────────────────────

    def logout(self):
        """Logout current user"""
        # print("[AUTH] Logging out...")
        username = self.get_current_user()
        result = self.session.end_session()
        if result:
            log_auth(username, 'logout', True)
            # print(f"[AUTH] ✅ Logged out: {username}")
        return result

    # ── Registration ──────────────────────────────────────────

    def start_registration(self, username, password, confirm_password,
                           language_code, language_name,
                           wake_word="hey deskmate"):
        """
        Start registration process
        Step 1 of registration
        Returns (success, message)
        """
        # print(f"[AUTH] Starting registration: {username}")
        log_info(f"Registration started: {username}")

        # Validate
        valid, message = self.registration.validate_new_user(
            username, password, confirm_password
        )
        if not valid:
            return False, message

        # Register basic info
        return self.registration.register_basic_info(
            username, password, language_code,
            language_name, wake_word
        )

    def register_face(self, username, progress_callback=None):
        """Register face for user"""
        # print(f"[AUTH] Registering face: {username}")
        return self.registration.register_face(username, progress_callback)

    def register_voice_password(self, username, passphrase,
                                 progress_callback=None):
        """Register voice password for user"""
        # print(f"[AUTH] Registering voice password: {username}")
        return self.registration.register_voice_password(
            username, passphrase, progress_callback
        )

    def register_speaker_profile(self, username, progress_callback=None):
        """Register speaker profile for user"""
        # print(f"[AUTH] Registering speaker profile: {username}")
        return self.registration.register_speaker_profile(
            username, progress_callback
        )

    def complete_registration(self, username):
        """Complete registration process"""
        # print(f"[AUTH] Completing registration: {username}")
        return self.registration.complete_registration(username)

    # ── Admin Operations ──────────────────────────────────────

    def verify_admin(self, admin_username, credential, auth_method='password'):
        """
        Verify admin credentials
        Required before adding/deleting users
        Returns (success, message)
        """
        # print(f"[AUTH] Admin verification: {admin_username}")
        log_info(f"Admin verification: {admin_username}")

        return self.registration.verify_admin_for_new_user(
            admin_username, credential, auth_method
        )

    def add_user_by_admin(self, admin_username, admin_password,
                          new_username, new_password, confirm_password,
                          language_code, language_name,
                          wake_word="hey deskmate"):
        """
        Add new user with admin authorization
        Returns (success, message)
        """
        # print(f"[AUTH] Admin adding user: {new_username} by {admin_username}")
        log_info(f"Admin {admin_username} adding user: {new_username}")

        # Verify admin first
        success, message = self.verify_admin(admin_username, admin_password)
        if not success:
            # print(f"[AUTH] Admin verification failed")
            return False, f"Admin verification failed: {message}"

        # Validate new user
        valid, msg = self.registration.validate_new_user(
            new_username, new_password, confirm_password
        )
        if not valid:
            return False, msg

        # Register basic info
        success, msg = self.registration.register_basic_info(
            new_username, new_password, language_code,
            language_name, wake_word
        )

        if success:
            # Set added_by
            self.registration.set_added_by(new_username, admin_username)
            # print(f"[AUTH] ✅ User added: {new_username} by {admin_username}")
            log_info(f"User {new_username} added by {admin_username}")

        return success, msg

    def delete_user(self, admin_username, admin_password, username):
        """
        Delete user with admin authorization
        Returns (success, message)
        """
        # print(f"[AUTH] Deleting user: {username} by {admin_username}")
        log_info(f"Delete user: {username} by {admin_username}")

        return self.registration.delete_user(
            username, admin_username, admin_password
        )

    # ── Settings Updates ──────────────────────────────────────

    def update_language(self, username, language_code, language_name):
        """Update user language"""
        # print(f"[AUTH] Updating language: {username}")
        success, message = self.registration.update_language(
            username, language_code, language_name
        )
        if success:
            self.session.update_language(language_code, language_name)
        return success, message

    def update_wake_word(self, username, wake_word, sensitivity=0.6):
        """Update user wake word"""
        # print(f"[AUTH] Updating wake word: {username}")
        success, message = self.registration.update_wake_word(
            username, wake_word, sensitivity
        )
        if success:
            self.session.update_wake_word(wake_word, sensitivity)
        return success, message

    def change_password(self, username, old_password, new_password):
        """Change user password"""
        # print(f"[AUTH] Changing password: {username}")
        return self.password_auth.change_password(
            username, old_password, new_password
        )

    def re_register_face(self, username, progress_callback=None):
        """Re-register face (replaces existing)"""
        # print(f"[AUTH] Re-registering face: {username}")
        self.face_auth.delete_face_data(username)
        return self.face_auth.register(username, progress_callback)

    def re_register_voice_password(self, username, passphrase,
                                    progress_callback=None):
        """Re-register voice password (replaces existing)"""
        # print(f"[AUTH] Re-registering voice password: {username}")
        self.speech_auth.delete_voice_password(username)
        from backend.utils.utils import load_profile as lp
        profile = lp(username)
        language = profile.get('language', 'en')
        return self.speech_auth.register_voice_password(
            username, passphrase, language, progress_callback
        )

    def add_face_sample(self, username):
        """Add extra face sample"""
        # print(f"[AUTH] Adding face sample: {username}")
        return self.face_auth.add_face_sample(username)

    def add_speaker_sample(self, username, progress_callback=None):
        """Add extra speaker sample"""
        # print(f"[AUTH] Adding speaker sample: {username}")
        return self.speech_auth.add_speaker_sample(username, progress_callback)

    # ── User Info ─────────────────────────────────────────────

    def get_all_users(self):
        """Get all registered users"""
        return self.registration.get_all_users()

    def get_registration_status(self, username):
        """Get registration status for user"""
        return self.registration.get_registration_status(username)

    def get_session_info(self):
        """Get current session info"""
        return self.session.get_session_info()

    def refresh_session(self):
        """Refresh session profile from disk"""
        return self.session.refresh_profile()


# ── Singleton Instance ────────────────────────────────────────

_auth_orchestrator = None

def get_auth_orchestrator():
    global _auth_orchestrator
    if _auth_orchestrator is None:
        # print("[AUTH] Creating singleton AuthOrchestrator...")
        _auth_orchestrator = AuthOrchestrator()
    return _auth_orchestrator
'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `is_first_run()` | Check if no users exist |
| `is_logged_in()` | Check login state |
| `login_with_password()` | Password login |
| `login_with_face()` | Face login |
| `login_with_voice()` | Voice password login |
| `login()` | Universal login router |
| `logout()` | End session |
| `start_registration()` | Begin registration |
| `register_face()` | Face step |
| `register_voice_password()` | Voice step |
| `register_speaker_profile()` | Speaker step |
| `complete_registration()` | Finish registration |
| `verify_admin()` | Admin verification |
| `add_user_by_admin()` | Admin adds new user |
| `delete_user()` | Admin deletes user |
| `update_language()` | Language change |
| `update_wake_word()` | Wake word change |
| `change_password()` | Password change |
| `re_register_face()` | Replace face data |
| `re_register_voice_password()` | Replace voice password |
| `get_auth_orchestrator()` | Singleton — creates once |

---

## How it connects to everything:
```
UI calls auth_orchestrator only
        ↓
auth_orchestrator coordinates:
├── password_auth.py
├── face_auth.py
├── speech_auth.py
├── registration.py
└── session_manager.py
        ↓
Returns result to UI
'''