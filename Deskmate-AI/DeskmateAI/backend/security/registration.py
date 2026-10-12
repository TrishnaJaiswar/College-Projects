# DeskmateAI/backend/security/registration.py

import os
import sys
import time

# ============================================================
# REGISTRATION MANAGER FOR DESKMATEAI
# Handles complete user registration flow
# Step 1: Basic info (username, password, language)
# Step 2: Face registration
# Step 3: Voice password registration
# Step 4: Speaker profile registration
# Creates user directory structure
# First user automatically becomes admin
# Subsequent users require admin authorization
# All data persists to JSON and .npy files
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.security.password_auth import get_password_auth
from backend.security.face_auth import get_face_auth
from backend.security.speech_auth import get_speech_auth
from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import (
    create_user_dirs,
    save_profile,
    load_profile,
    list_users,
    user_exists,
    get_timestamp,
    validate_username,
    validate_password,
    is_first_run,
    get_admin_user,
    SUPPORTED_LANGUAGES
)

# ── Registration Steps ────────────────────────────────────────

REGISTRATION_STEPS = [
    "basic_info",
    "face_registration",
    "voice_password",
    "speaker_profile",
    "complete"
]

# ── Registration Manager ──────────────────────────────────────

class RegistrationManager:

    def __init__(self):
        # print("[REGISTRATION] Initializing RegistrationManager...")
        self.password_auth = get_password_auth()
        self.face_auth = get_face_auth()
        self._speech_auth = None  # Lazy load
        self._current_registration = None
        log_info("RegistrationManager initialized")

    @property
    def speech_auth(self):
        """Lazy load to prevent blocking"""
        if self._speech_auth is None:
            self._speech_auth = get_speech_auth()
        return self._speech_auth

    # ── Check First Run ───────────────────────────────────────

    def is_first_run(self):
        """Check if this is first time running (no users exist)"""
        result = is_first_run()
        # print(f"[REGISTRATION] Is first run: {result}")
        return result

    # ── Validate New User ─────────────────────────────────────

    def validate_new_user(self, username, password, confirm_password):
        """
        Validate new user information before registration
        Returns (valid, message)
        """
        # print(f"[REGISTRATION] Validating new user: {username}")

        # Validate username
        valid, message = validate_username(username)
        if not valid:
            # print(f"[REGISTRATION] Invalid username: {message}")
            return False, message

        # Check if username already exists
        if user_exists(username):
            # print(f"[REGISTRATION] Username taken: {username}")
            return False, f"Username '{username}' already exists"

        # Validate password
        valid, message = validate_password(password)
        if not valid:
            # print(f"[REGISTRATION] Invalid password: {message}")
            return False, message

        # Check passwords match
        if password != confirm_password:
            # print("[REGISTRATION] Passwords don't match")
            return False, "Passwords do not match"

        # print(f"[REGISTRATION] ✅ Validation passed: {username}")
        return True, "Valid"

    # ── Step 1: Register Basic Info ───────────────────────────

    def register_basic_info(self, username, password, language_code,
                             language_name, wake_word="hey deskmate"):
        """
        Step 1: Register basic user information
        Creates user directory structure
        Saves initial profile
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Step 1 - Basic info: {username}")
        log_info(f"Registration Step 1: {username}")

        try:
            # Determine if admin
            is_admin = is_first_run()
            # print(f"[REGISTRATION] Is admin: {is_admin}")

            # Create user directories
            create_user_dirs(username)
            # print(f"[REGISTRATION] ✅ Directories created: {username}")

            # Create initial profile
            profile = {
                "username": username,
                "password_hash": None,
                "language": language_code,
                "language_name": language_name,
                "wake_word": wake_word.lower().strip(),
                "wake_word_sensitivity": 0.6,
                "is_admin": is_admin,
                "added_by": "self" if is_admin else None,
                "registered_at": get_timestamp(),
                "last_login": None,
                "auth_methods": [],
                "face_samples": 0,
                "speaker_samples": 0,
                "voice_passphrase": None,
                "voice_passphrase_language": language_code,
                "registration_complete": False
            }

            # Save profile
            save_profile(username, profile)
            # print(f"[REGISTRATION] ✅ Initial profile saved: {username}")

            # Register password
            success, message = self.password_auth.register_password(
                username, password
            )

            if not success:
                # print(f"[REGISTRATION] ❌ Password registration failed: {message}")
                log_error(f"Password registration failed: {message}")
                return False, message

            # print(f"[REGISTRATION] ✅ Step 1 complete: {username}")
            log_info(f"Registration Step 1 complete: {username}")
            return True, "Basic info registered"

        except Exception as e:
            # print(f"[REGISTRATION] Step 1 error: {e}")
            log_error(f"Registration Step 1 error: {e}")
            return False, str(e)

    # ── Step 2: Register Face ─────────────────────────────────

    def register_face(self, username, progress_callback=None):
        """
        Step 2: Register face authentication
        Captures 3 face samples
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Step 2 - Face: {username}")
        log_info(f"Registration Step 2 - Face: {username}")

        try:
            success, message = self.face_auth.register(
                username,
                progress_callback=progress_callback
            )

            if success:
                # print(f"[REGISTRATION] ✅ Step 2 complete: {username}")
                log_info(f"Face registration complete: {username}")
            else:
                # print(f"[REGISTRATION] ❌ Step 2 failed: {message}")
                log_warning(f"Face registration failed: {message}")

            return success, message

        except Exception as e:
            # print(f"[REGISTRATION] Step 2 error: {e}")
            log_error(f"Registration Step 2 error: {e}")
            return False, str(e)

    # ── Step 3: Register Voice Password ──────────────────────

    def register_voice_password(self, username, passphrase,
                                 progress_callback=None):
        """
        Step 3: Register voice password
        Records passphrase 3 times
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Step 3 - Voice password: {username}")
        log_info(f"Registration Step 3 - Voice password: {username}")

        try:
            # Get language from profile
            profile = load_profile(username)
            language = profile.get('language', 'en')

            success, message = self.speech_auth.register_voice_password(
                username=username,
                passphrase=passphrase,
                language=language,
                progress_callback=progress_callback
            )

            if success:
                # print(f"[REGISTRATION] ✅ Step 3 complete: {username}")
                log_info(f"Voice password registration complete: {username}")
            else:
                # print(f"[REGISTRATION] ❌ Step 3 failed: {message}")
                log_warning(f"Voice password registration failed: {message}")

            return success, message

        except Exception as e:
            # print(f"[REGISTRATION] Step 3 error: {e}")
            log_error(f"Registration Step 3 error: {e}")
            return False, str(e)

    # ── Step 4: Register Speaker Profile ─────────────────────

    def register_speaker_profile(self, username, progress_callback=None):
        """
        Step 4: Register speaker profile
        Records 3 voice samples for verification
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Step 4 - Speaker profile: {username}")
        log_info(f"Registration Step 4 - Speaker: {username}")

        try:
            success, message = self.speech_auth.register_speaker_profile(
                username,
                progress_callback=progress_callback
            )

            if success:
                # print(f"[REGISTRATION] ✅ Step 4 complete: {username}")
                log_info(f"Speaker registration complete: {username}")
            else:
                # print(f"[REGISTRATION] ❌ Step 4 failed: {message}")
                log_warning(f"Speaker registration failed: {message}")

            return success, message

        except Exception as e:
            # print(f"[REGISTRATION] Step 4 error: {e}")
            log_error(f"Registration Step 4 error: {e}")
            return False, str(e)

    # ── Complete Registration ─────────────────────────────────

    def complete_registration(self, username):
        """
        Mark registration as complete
        Called after all steps done
        """
        # print(f"[REGISTRATION] Completing registration: {username}")
        log_info(f"Completing registration: {username}")

        try:
            profile = load_profile(username)
            profile['registration_complete'] = True
            profile['registration_completed_at'] = get_timestamp()
            save_profile(username, profile)

            # print(f"[REGISTRATION] ✅ Registration complete: {username}")
            log_info(f"Registration complete: {username}")
            return True, "Registration completed successfully"

        except Exception as e:
            # print(f"[REGISTRATION] Complete error: {e}")
            log_error(f"Complete registration error: {e}")
            return False, str(e)

    # ── Full Registration Flow ────────────────────────────────

    def register_full(self, username, password, confirm_password,
                      language_code, language_name, passphrase,
                      wake_word="hey deskmate",
                      face_progress_cb=None,
                      voice_progress_cb=None,
                      speaker_progress_cb=None):
        """
        Complete registration in one call
        Used for non-UI registration
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Full registration: {username}")
        log_info(f"Full registration started: {username}")

        # Validate
        valid, message = self.validate_new_user(
            username, password, confirm_password
        )
        if not valid:
            return False, message

        # Step 1
        success, msg = self.register_basic_info(
            username, password, language_code,
            language_name, wake_word
        )
        if not success:
            return False, f"Step 1 failed: {msg}"

        # Step 2
        success, msg = self.register_face(
            username, face_progress_cb
        )
        if not success:
            log_warning(f"Face registration failed: {msg}")
            # Continue - face is optional

        # Step 3
        success, msg = self.register_voice_password(
            username, passphrase, voice_progress_cb
        )
        if not success:
            log_warning(f"Voice password failed: {msg}")
            # Continue - voice password is optional

        # Step 4
        success, msg = self.register_speaker_profile(
            username, speaker_progress_cb
        )
        if not success:
            log_warning(f"Speaker profile failed: {msg}")
            # Continue - speaker profile is optional

        # Complete
        self.complete_registration(username)

        # print(f"[REGISTRATION] ✅ Full registration done: {username}")
        log_info(f"Full registration done: {username}")
        return True, "Registration completed"

    # ── Admin Authorization for New User ──────────────────────

    def verify_admin_for_new_user(self, admin_username, admin_credential,
                                   auth_method='password'):
        """
        Verify admin credentials before adding new user
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Admin verification: {admin_username}")
        log_info(f"Admin verification for new user by: {admin_username}")

        try:
            # Check if user is admin
            profile = load_profile(admin_username)
            if not profile:
                return False, "Admin user not found"

            if not profile.get('is_admin', False):
                # print(f"[REGISTRATION] Not admin: {admin_username}")
                return False, "Only admin can add new users"

            # Verify admin credentials
            if auth_method == 'password':
                success, message = self.password_auth.authenticate(
                    admin_username, admin_credential
                )
            elif auth_method == 'face':
                success = self.face_auth.verify(admin_username)
                message = "Face verified" if success else "Face verification failed"
            elif auth_method == 'voice':
                success, message = self.speech_auth.login_with_voice_password(
                    admin_username
                )
            else:
                return False, "Invalid auth method"

            if success:
                # print(f"[REGISTRATION] ✅ Admin verified: {admin_username}")
                log_info(f"Admin verified: {admin_username}")
            else:
                # print(f"[REGISTRATION] ❌ Admin verification failed")
                log_warning(f"Admin verification failed: {admin_username}")

            return success, message

        except Exception as e:
            # print(f"[REGISTRATION] Admin verify error: {e}")
            log_error(f"Admin verification error: {e}")
            return False, str(e)

    # ── Set Added By ──────────────────────────────────────────

    def set_added_by(self, username, admin_username):
        """Record which admin added this user"""
        # print(f"[REGISTRATION] Setting added_by: {username} by {admin_username}")
        try:
            profile = load_profile(username)
            profile['added_by'] = admin_username
            save_profile(username, profile)
            log_debug(f"Set added_by: {username} → {admin_username}")
            return True
        except Exception as e:
            log_error(f"Set added_by error: {e}")
            return False

    # ── Delete User ───────────────────────────────────────────

    def delete_user(self, username, admin_username, admin_password):
        """
        Delete user (admin only)
        Removes all user data
        Returns (success, message)
        """
        # print(f"[REGISTRATION] Deleting user: {username} by {admin_username}")
        log_info(f"Delete user: {username} by {admin_username}")

        try:
            # Verify admin
            success, message = self.password_auth.authenticate(
                admin_username, admin_password
            )
            if not success:
                return False, "Admin authentication failed"

            # Check admin privileges
            admin_profile = load_profile(admin_username)
            if not admin_profile.get('is_admin', False):
                return False, "Only admin can delete users"

            # Cannot delete self
            if username == admin_username:
                return False, "Cannot delete your own account"

            # Delete user directories
            from backend.utils.utils import delete_user_dirs
            result = delete_user_dirs(username)

            if result:
                # print(f"[REGISTRATION] ✅ User deleted: {username}")
                log_info(f"User deleted: {username}")
                return True, f"User '{username}' deleted successfully"
            else:
                return False, "Failed to delete user data"

        except Exception as e:
            # print(f"[REGISTRATION] Delete user error: {e}")
            log_error(f"Delete user error: {e}")
            return False, str(e)

    # ── Get Registration Status ───────────────────────────────

    def get_registration_status(self, username):
        """
        Get detailed registration status for user
        Shows which steps are complete
        """
        # print(f"[REGISTRATION] Getting status: {username}")
        try:
            profile = load_profile(username)
            if not profile:
                return None

            status = {
                "username": username,
                "basic_info": bool(profile.get('password_hash')),
                "face_registered": self.face_auth.is_registered(username),
                "voice_password": self.speech_auth.is_voice_password_registered(username),
                "speaker_profile": self.speech_auth.is_speaker_registered(username),
                "registration_complete": profile.get('registration_complete', False),
                "auth_methods": profile.get('auth_methods', []),
                "is_admin": profile.get('is_admin', False),
                "language": profile.get('language', 'en'),
                "language_name": profile.get('language_name', 'English'),
                "wake_word": profile.get('wake_word', 'hey deskmate'),
                "registered_at": profile.get('registered_at'),
                "last_login": profile.get('last_login')
            }

            # print(f"[REGISTRATION] Status: {status}")
            return status

        except Exception as e:
            # print(f"[REGISTRATION] Status error: {e}")
            log_error(f"Get registration status error: {e}")
            return None

    # ── Get All Users ─────────────────────────────────────────

    def get_all_users(self):
        """Get list of all registered users with basic info"""
        # print("[REGISTRATION] Getting all users...")
        try:
            users = list_users()
            user_list = []

            for username in users:
                profile = load_profile(username)
                if profile:
                    user_list.append({
                        "username": username,
                        "is_admin": profile.get('is_admin', False),
                        "language": profile.get('language', 'en'),
                        "language_name": profile.get('language_name', 'English'),
                        "registered_at": profile.get('registered_at'),
                        "last_login": profile.get('last_login'),
                        "registration_complete": profile.get('registration_complete', False),
                        "auth_methods": profile.get('auth_methods', []),
                        "added_by": profile.get('added_by', 'self')
                    })

            # print(f"[REGISTRATION] Found {len(user_list)} users")
            return user_list

        except Exception as e:
            # print(f"[REGISTRATION] Get users error: {e}")
            log_error(f"Get all users error: {e}")
            return []

    # ── Update User Settings ──────────────────────────────────

    def update_language(self, username, language_code, language_name):
        """Update user language setting"""
        # print(f"[REGISTRATION] Updating language: {username} → {language_code}")
        log_info(f"Language update: {username} → {language_code}")
        try:
            profile = load_profile(username)
            old_language = profile.get('language')
            profile['language'] = language_code
            profile['language_name'] = language_name
            save_profile(username, profile)

            # Warn if voice password language differs
            voice_pass_language = profile.get('voice_passphrase_language')
            if voice_pass_language and voice_pass_language != language_code:
                log_warning(
                    f"Voice password registered in {voice_pass_language} "
                    f"but language changed to {language_code}"
                )
                return True, (
                    f"Language updated. Note: Your voice password was "
                    f"registered in {voice_pass_language}. "
                    f"Please re-register your voice password."
                )

            # print(f"[REGISTRATION] ✅ Language updated: {username}")
            return True, "Language updated successfully"

        except Exception as e:
            # print(f"[REGISTRATION] Language update error: {e}")
            log_error(f"Language update error: {e}")
            return False, str(e)

    def update_wake_word(self, username, wake_word, sensitivity=0.6):
        """Update user wake word"""
        # print(f"[REGISTRATION] Updating wake word: {username} → {wake_word}")
        log_info(f"Wake word update: {username} → {wake_word}")
        try:
            profile = load_profile(username)
            profile['wake_word'] = wake_word.lower().strip()
            profile['wake_word_sensitivity'] = sensitivity
            save_profile(username, profile)
            # print(f"[REGISTRATION] ✅ Wake word updated: {username}")
            return True, "Wake word updated successfully"
        except Exception as e:
            # print(f"[REGISTRATION] Wake word update error: {e}")
            log_error(f"Wake word update error: {e}")
            return False, str(e)


# ── Singleton Instance ────────────────────────────────────────

_registration_manager = None

def get_registration_manager():
    global _registration_manager
    if _registration_manager is None:
        # print("[REGISTRATION] Creating singleton RegistrationManager...")
        _registration_manager = RegistrationManager()
    return _registration_manager
'''
```

---

## What this file does:

| Function | Purpose |
|---|---|
| `is_first_run()` | Check if no users exist |
| `validate_new_user()` | Validate username/password |
| `register_basic_info()` | Step 1 — profile + password |
| `register_face()` | Step 2 — face samples |
| `register_voice_password()` | Step 3 — voice passphrase |
| `register_speaker_profile()` | Step 4 — speaker samples |
| `complete_registration()` | Mark registration done |
| `register_full()` | All steps in one call |
| `verify_admin_for_new_user()` | Admin auth before adding user |
| `set_added_by()` | Track who added user |
| `delete_user()` | Admin only user deletion |
| `get_registration_status()` | Check all steps status |
| `get_all_users()` | List all users with info |
| `update_language()` | Change language with warning |
| `update_wake_word()` | Change wake word |
| `get_registration_manager()` | Singleton — creates once |

---

## Registration flow:
```
First run → No admin check needed
        ↓
Step 1: username + password + language
        ↓
Step 2: Face (3 samples)
        ↓
Step 3: Voice password (3 recordings)
        ↓
Step 4: Speaker profile (3 recordings)
        ↓
Complete ✅

Adding new user → Admin must verify first
        ↓
Same 4 steps
        ↓
Added by = admin username ✅
'''