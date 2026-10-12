# DeskmateAI/backend/security/password_auth.py

import os
import sys

# ============================================================
# PASSWORD AUTHENTICATION FOR DESKMATEAI
# Handles password hashing and verification
# Uses bcrypt for secure one-way hashing
# Passwords never stored in plain text
# All data persists in user profile JSON
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning
from backend.utils.utils import (
    load_profile,
    save_profile,
    get_profile_path,
    get_timestamp,
    validate_password
)

# ── Password Auth Class ───────────────────────────────────────

class PasswordAuth:

    def __init__(self):
        # print("[PASSWORD] Initializing PasswordAuth...")
        self._bcrypt = None
        self._load_bcrypt()
        log_info("PasswordAuth initialized")

    def _load_bcrypt(self):
        """Load bcrypt library"""
        # print("[PASSWORD] Loading bcrypt...")
        try:
            import bcrypt
            self._bcrypt = bcrypt
            # print("[PASSWORD] ✅ bcrypt loaded")
            log_debug("bcrypt loaded successfully")
        except ImportError:
            # print("[PASSWORD] ❌ bcrypt not found, installing...")
            log_error("bcrypt not installed. Run: pip install bcrypt")
            self._bcrypt = None

    # ── Hash Password ─────────────────────────────────────────

    def hash_password(self, password):
        """
        Hash password using bcrypt
        Returns hashed password as string
        Never stores plain text
        """
        # print("[PASSWORD] Hashing password...")
        try:
            if not self._bcrypt:
                self._load_bcrypt()

            if not self._bcrypt:
                log_error("bcrypt not available")
                return None

            # Validate password
            valid, message = validate_password(password)
            if not valid:
                log_warning(f"Invalid password: {message}")
                return None

            # Generate salt and hash
            password_bytes = password.encode('utf-8')
            salt = self._bcrypt.gensalt(rounds=12)
            hashed = self._bcrypt.hashpw(password_bytes, salt)

            # Return as string for JSON storage
            hashed_str = hashed.decode('utf-8')
            # print("[PASSWORD] ✅ Password hashed successfully")
            log_debug("Password hashed successfully")
            return hashed_str

        except Exception as e:
            # print(f"[PASSWORD] Hash error: {e}")
            log_error(f"Password hash error: {e}")
            return None

    # ── Verify Password ───────────────────────────────────────

    def verify_password(self, plain_password, hashed_password):
        """
        Verify plain password against stored hash
        Returns True if match, False otherwise
        """
        # print("[PASSWORD] Verifying password...")
        try:
            if not self._bcrypt:
                self._load_bcrypt()

            if not self._bcrypt:
                log_error("bcrypt not available")
                return False

            if not plain_password or not hashed_password:
                # print("[PASSWORD] Empty password or hash")
                return False

            # Convert to bytes
            password_bytes = plain_password.encode('utf-8')
            if isinstance(hashed_password, str):
                hashed_bytes = hashed_password.encode('utf-8')
            else:
                hashed_bytes = hashed_password

            # Verify
            result = self._bcrypt.checkpw(password_bytes, hashed_bytes)
            # print(f"[PASSWORD] Verification result: {result}")
            log_debug(f"Password verification: {'success' if result else 'failed'}")
            return result

        except Exception as e:
            # print(f"[PASSWORD] Verify error: {e}")
            log_error(f"Password verify error: {e}")
            return False

    # ── Register User Password ────────────────────────────────

    def register_password(self, username, password):
        """
        Register password for user
        Hashes and saves to profile
        """
        # print(f"[PASSWORD] Registering password for: {username}")
        log_info(f"Registering password for: {username}")

        try:
            # Validate
            valid, message = validate_password(password)
            if not valid:
                # print(f"[PASSWORD] Invalid password: {message}")
                log_warning(f"Invalid password: {message}")
                return False, message

            # Hash password
            hashed = self.hash_password(password)
            if not hashed:
                return False, "Failed to hash password"

            # Save to profile
            profile = load_profile(username)
            profile['password_hash'] = hashed
            profile['password_registered_at'] = get_timestamp()

            if 'password' not in profile.get('auth_methods', []):
                profile.setdefault('auth_methods', []).append('password')

            save_profile(username, profile)
            # print(f"[PASSWORD] ✅ Password registered for: {username}")
            log_info(f"Password registered for: {username}")
            return True, "Password registered successfully"

        except Exception as e:
            # print(f"[PASSWORD] Register error: {e}")
            log_error(f"Register password error: {e}")
            return False, str(e)

    # ── Authenticate User ─────────────────────────────────────

    def authenticate(self, username, password):
        """
        Authenticate user with username and password
        Returns (success, message)
        """
        # print(f"[PASSWORD] Authenticating: {username}")
        log_info(f"Password auth attempt: {username}")

        try:
            # Load profile
            profile = load_profile(username)
            if not profile:
                # print(f"[PASSWORD] User not found: {username}")
                log_warning(f"User not found: {username}")
                return False, "User not found"

            # Check if password auth is registered
            if 'password' not in profile.get('auth_methods', []):
                # print(f"[PASSWORD] Password auth not registered for: {username}")
                log_warning(f"Password auth not registered: {username}")
                return False, "Password authentication not set up"

            # Get stored hash
            stored_hash = profile.get('password_hash')
            if not stored_hash:
                # print(f"[PASSWORD] No password hash found for: {username}")
                log_warning(f"No password hash: {username}")
                return False, "No password registered"

            # Verify
            if self.verify_password(password, stored_hash):
                # print(f"[PASSWORD] ✅ Authentication successful: {username}")
                log_info(f"Password auth successful: {username}")
                return True, "Authentication successful"
            else:
                # print(f"[PASSWORD] ❌ Wrong password: {username}")
                log_warning(f"Wrong password: {username}")
                return False, "Incorrect password"

        except Exception as e:
            # print(f"[PASSWORD] Auth error: {e}")
            log_error(f"Password auth error: {e}")
            return False, str(e)

    # ── Change Password ───────────────────────────────────────

    def change_password(self, username, old_password, new_password):
        """
        Change user password
        Requires old password verification
        """
        # print(f"[PASSWORD] Changing password for: {username}")
        log_info(f"Password change attempt: {username}")

        try:
            # Verify old password first
            success, message = self.authenticate(username, old_password)
            if not success:
                # print(f"[PASSWORD] Old password wrong: {username}")
                return False, "Current password is incorrect"

            # Validate new password
            valid, msg = validate_password(new_password)
            if not valid:
                return False, msg

            # Check new password different from old
            if old_password == new_password:
                return False, "New password must be different"

            # Register new password
            success, message = self.register_password(username, new_password)
            if success:
                # print(f"[PASSWORD] ✅ Password changed: {username}")
                log_info(f"Password changed successfully: {username}")
                return True, "Password changed successfully"
            return False, message

        except Exception as e:
            # print(f"[PASSWORD] Change error: {e}")
            log_error(f"Change password error: {e}")
            return False, str(e)

    # ── Reset Password ────────────────────────────────────────

    def reset_password(self, username, new_password, admin_username, admin_password):
        """
        Reset user password (admin only)
        Requires admin credentials
        """
        # print(f"[PASSWORD] Reset password for: {username} by admin: {admin_username}")
        log_info(f"Password reset: {username} by {admin_username}")

        try:
            # Verify admin
            admin_success, msg = self.authenticate(admin_username, admin_password)
            if not admin_success:
                # print(f"[PASSWORD] Admin auth failed")
                return False, "Admin authentication failed"

            # Check admin privileges
            from backend.utils.utils import load_profile as lp
            admin_profile = lp(admin_username)
            if not admin_profile.get('is_admin', False):
                # print(f"[PASSWORD] Not admin: {admin_username}")
                return False, "Only admin can reset passwords"

            # Set new password
            success, message = self.register_password(username, new_password)
            if success:
                # print(f"[PASSWORD] ✅ Password reset: {username}")
                log_info(f"Password reset successful: {username}")
                return True, "Password reset successfully"
            return False, message

        except Exception as e:
            # print(f"[PASSWORD] Reset error: {e}")
            log_error(f"Reset password error: {e}")
            return False, str(e)

    # ── Check Password Registered ─────────────────────────────

    def is_password_registered(self, username):
        """Check if user has password registered"""
        # print(f"[PASSWORD] Checking registration: {username}")
        try:
            profile = load_profile(username)
            registered = bool(profile.get('password_hash'))
            # print(f"[PASSWORD] Password registered: {registered}")
            return registered
        except Exception as e:
            # print(f"[PASSWORD] Check error: {e}")
            log_error(f"Check password registered error: {e}")
            return False

    # ── Validate Strength ─────────────────────────────────────

    def check_password_strength(self, password):
        """
        Check password strength
        Returns (strength, message)
        strength: 'weak', 'medium', 'strong'
        """
        # print(f"[PASSWORD] Checking strength...")
        if not password:
            return 'weak', 'Password is empty'

        score = 0
        feedback = []

        # Length check
        if len(password) >= 8:
            score += 1
        else:
            feedback.append("At least 8 characters")

        if len(password) >= 12:
            score += 1

        # Character variety
        if any(c.isupper() for c in password):
            score += 1
        else:
            feedback.append("Add uppercase letters")

        if any(c.islower() for c in password):
            score += 1
        else:
            feedback.append("Add lowercase letters")

        if any(c.isdigit() for c in password):
            score += 1
        else:
            feedback.append("Add numbers")

        if any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            score += 1
        else:
            feedback.append("Add special characters")

        if score <= 2:
            strength = 'weak'
        elif score <= 4:
            strength = 'medium'
        else:
            strength = 'strong'

        message = ', '.join(feedback) if feedback else f"Password is {strength}"
        # print(f"[PASSWORD] Strength: {strength}")
        return strength, message


# ── Singleton Instance ────────────────────────────────────────

_password_auth = None

def get_password_auth():
    global _password_auth
    if _password_auth is None:
        # print("[PASSWORD] Creating singleton PasswordAuth...")
        _password_auth = PasswordAuth()
    return _password_auth