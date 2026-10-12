# DeskmateAI/ui/views/login_window.py

import os
import sys
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QScrollArea,
    QGraphicsDropShadowEffect, QSizePolicy
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation,
    QEasingCurve, QSize
)
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen,
    QLinearGradient, QPixmap, QIcon
)

# ============================================================
# LOGIN WINDOW FOR DESKMATEAI
# Matches Image 1 design exactly
# Features:
# - Auto voice login (listens immediately on open)
# - User avatar cards with name
# - Click user → shows auth method selection
# - Auth methods: Voice Password, Type Password, Face
# - Add New User card
# - Fully styled in dark cyan theme
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ui.animations.waveform import SmallWaveformWidget
from ui.animations.status_indicator import StatusLabel
from backend.utils.logger import log_info, log_error, log_debug

# ── Colors ────────────────────────────────────────────────────

C = {
    "bg":       "#0D1117",
    "surface":  "#161B22",
    "surface2": "#1C2128",
    "border":   "#30363D",
    "accent":   "#00D4FF",
    "text":     "#E6EDF3",
    "subtext":  "#8B949E",
    "success":  "#3FB950",
    "error":    "#F85149",
}

# ── Voice Login Thread ────────────────────────────────────────

class VoiceLoginThread(QThread):
    login_success = pyqtSignal(str, str)
    login_failed  = pyqtSignal(str)
    listening_started = pyqtSignal()

    def __init__(self, users_data, parent=None):
        # users_data = list of (username, profile_dict) tuples
        # loaded on main thread BEFORE this thread starts
        super().__init__(parent)
        self._users_data = users_data   # <-- pre-loaded, no file I/O in thread
        self._running    = False

    def run(self):
        import os
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        os.environ['OMP_NUM_THREADS']       = '1'
        os.environ['OPENBLAS_NUM_THREADS']  = '1'
        os.environ['MKL_NUM_THREADS']       = '1'

        self._running = True
        self.listening_started.emit()

        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()

            while self._running:
                for username, profile in self._users_data:
                    if not self._running:
                        break
                    if 'voice' not in profile.get('auth_methods', []):
                        continue

                    success, message, user_profile = auth.login(username, 'voice')

                    if success and self._running:
                        from backend.utils.logger import log_info
                        log_info(f"Voice auto-login: {username}")
                        self.login_success.emit(username, 'voice')
                        return

        except Exception as e:
            from backend.utils.logger import log_error
            log_error(f"Voice login thread error: {e}")
            self.login_failed.emit(str(e))

    def stop(self):
        self._running = False

# ── User Avatar Card ──────────────────────────────────────────

class UserAvatarCard(QWidget):
    """
    User avatar card widget
    Shows initial letter + username
    Cyan glow on hover
    Matches Image 1 user cards
    """
    clicked = pyqtSignal(str)  # username

    def __init__(self, username, is_admin=False, parent=None):
        super().__init__(parent)
        self.username = username
        self.is_admin = is_admin
        self._hovered = False

        self.setFixedSize(80, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMouseTracking(True)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Avatar circle
        self._avatar = QLabel(username[0].upper())
        self._avatar.setFixedSize(50, 50)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_avatar_style(False)
        layout.addWidget(self._avatar, 0, Qt.AlignmentFlag.AlignCenter)

        # Username
        display_name = username[:8] + ".." if len(username) > 8 else username
        name_label = QLabel(display_name)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name_label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(name_label)

        # print(f"[USER_CARD] Created: {username}")

    def _update_avatar_style(self, hovered):
        """Update avatar circle style"""
        if hovered:
            self._avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: {C['surface2']};
                    border: 2px solid {C['accent']};
                    border-radius: 25px;
                    color: {C['accent']};
                    font-size: 20px;
                    font-weight: bold;
                    font-family: 'Segoe UI';
                }}
            """)
        else:
            self._avatar.setStyleSheet(f"""
                QLabel {{
                    background-color: {C['surface2']};
                    border: 2px solid {C['border']};
                    border-radius: 25px;
                    color: {C['text']};
                    font-size: 20px;
                    font-weight: bold;
                    font-family: 'Segoe UI';
                }}
            """)

    def enterEvent(self, event):
        self._hovered = True
        self._update_avatar_style(True)

    def leaveEvent(self, event):
        self._hovered = False
        self._update_avatar_style(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            # print(f"[USER_CARD] Clicked: {self.username}")
            self.clicked.emit(self.username)


# ── Add User Card ─────────────────────────────────────────────

class AddUserCard(QWidget):
    """
    Add new user card (dashed circle with +)
    Matches Image 1 Add New card
    """
    clicked = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._hovered = False
        self.setFixedSize(80, 90)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(8)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Plus circle
        self._circle = QLabel("+")
        self._circle.setFixedSize(50, 50)
        self._circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._update_style(False)
        layout.addWidget(self._circle, 0, Qt.AlignmentFlag.AlignCenter)

        # Label
        add_label = QLabel("Add New")
        add_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        add_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(add_label)

    def _update_style(self, hovered):
        color = C['accent'] if hovered else C['subtext']
        self._circle.setStyleSheet(f"""
            QLabel {{
                background-color: transparent;
                border: 2px dashed {color};
                border-radius: 25px;
                color: {color};
                font-size: 22px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
        """)

    def enterEvent(self, event):
        self._hovered = True
        self._update_style(True)

    def leaveEvent(self, event):
        self._hovered = False
        self._update_style(False)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit()


# ── Auth Method Button ────────────────────────────────────────

class AuthMethodButton(QPushButton):
    """Auth method selection button"""

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon}  {text}")
        self.setFixedHeight(46)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                text-align: left;
                padding-left: 12px;
            }}
            QPushButton:hover {{
                background-color: {C['surface']};
                border: 1px solid {C['accent']};
                color: {C['accent']};
            }}
            QPushButton:pressed {{
                background-color: #0D2030;
            }}
        """)

class LoginAuthThread(QThread):
    auth_success = pyqtSignal(str, str, object)
    auth_failed  = pyqtSignal(str)

    def __init__(self, auth, username, method, credential=None, parent=None):
        super().__init__(parent)
        self._auth       = auth
        self._username   = username
        self._method     = method
        self._credential = credential

    def run(self):
        import os
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        os.environ['OMP_NUM_THREADS']       = '1'
        try:
            success, message, profile = self._auth.login(
                self._username, self._method, self._credential
            )
            if success:
                self.auth_success.emit(self._username, self._method, profile)
            else:
                self.auth_failed.emit(message)
        except Exception as e:
            self.auth_failed.emit(str(e))
# ── Login Window ──────────────────────────────────────────────

class LoginWindow(QWidget):
    """
    Main login window
    Matches Image 1 design exactly
    Auto-listens for voice password on open
    """

    # Signals
    login_success = pyqtSignal(str, str, object)  # username, method, profile
    register_requested = pyqtSignal()
    admin_add_user = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._selected_user = None
        self._voice_thread = None
        self._auth_thread  = None
        self._auth_orchestrator = None

        self._setup_window()
        self._setup_ui()
        self._load_users()
        #self._start_voice_login()

        log_info("LoginWindow initialized")
        # print("[LOGIN] LoginWindow initialized")

    def _setup_window(self):
        """Configure window properties"""
        self.setWindowTitle("DeskmateAI")
        self.setFixedSize(480, 580)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; }}")

    def _setup_ui(self):
        """Build UI matching Image 1"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 24, 30, 20)
        main_layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────
        header = QHBoxLayout()
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Mic icon circle
        mic_circle = QLabel("🎙")
        mic_circle.setFixedSize(44, 44)
        mic_circle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        mic_circle.setStyleSheet(f"""
            QLabel {{
                background-color: {C['surface2']};
                border: 1px solid {C['accent']};
                border-radius: 22px;
                font-size: 20px;
            }}
        """)
        header.addWidget(mic_circle)
        header.addSpacing(10)

        # Title
        title = QLabel("DeskmateAI")
        title.setStyleSheet(f"""
            QLabel {{
                color: {C['accent']};
                font-size: 26px;
                font-weight: bold;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        header.addWidget(title)

        main_layout.addLayout(header)
        main_layout.addSpacing(6)

        # Subtitle
        subtitle = QLabel("Your Voice. Your Control.")
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(subtitle)
        main_layout.addSpacing(20)

        # ── Voice Login Card ──────────────────────────────
        voice_card = QFrame()
        voice_card.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        voice_card_layout = QVBoxLayout(voice_card)
        voice_card_layout.setContentsMargins(20, 20, 20, 20)
        voice_card_layout.setSpacing(12)
        voice_card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Waveform
        self._waveform = SmallWaveformWidget()
        self._waveform.setFixedSize(260, 40)
        voice_card_layout.addWidget(
            self._waveform,
            0, Qt.AlignmentFlag.AlignCenter
        )

        # Voice status text
        self._voice_status = QLabel("Say your voice password to login")
        self._voice_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._voice_status.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        voice_card_layout.addWidget(self._voice_status)

        main_layout.addWidget(voice_card)
        main_layout.addSpacing(20)

        # ── Divider ────────────────────────────────────────
        divider_layout = QHBoxLayout()
        left_line = QFrame()
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setStyleSheet(f"color: {C['border']};")
        divider_layout.addWidget(left_line)

        divider_text = QLabel("or select user")
        divider_text.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                padding: 0 10px;
                background: transparent;
                border: none;
            }}
        """)
        divider_layout.addWidget(divider_text)

        right_line = QFrame()
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setStyleSheet(f"color: {C['border']};")
        divider_layout.addWidget(right_line)

        main_layout.addLayout(divider_layout)
        main_layout.addSpacing(16)

        # ── User Cards Row ─────────────────────────────────
        self._users_layout = QHBoxLayout()
        self._users_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._users_layout.setSpacing(12)
        main_layout.addLayout(self._users_layout)
        main_layout.addSpacing(16)

        # ── Auth Method Panel ──────────────────────────────
        # (shown when user is selected)
        self._auth_panel = QFrame()
        self._auth_panel.setVisible(False)
        self._auth_panel.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 12px;
            }}
        """)
        auth_panel_layout = QVBoxLayout(self._auth_panel)
        auth_panel_layout.setContentsMargins(16, 14, 16, 14)
        auth_panel_layout.setSpacing(8)

        # Selected user label
        self._selected_label = QLabel("Login as: ")
        self._selected_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        auth_panel_layout.addWidget(self._selected_label)

        # Auth method buttons
        self._voice_btn = AuthMethodButton("🎤", "Voice Password")
        self._voice_btn.clicked.connect(
            lambda: self._login_with_method('voice')
        )
        auth_panel_layout.addWidget(self._voice_btn)

        self._password_btn = AuthMethodButton("🔑", "Type Password")
        self._password_btn.clicked.connect(self._show_password_input)
        auth_panel_layout.addWidget(self._password_btn)

        self._face_btn = AuthMethodButton("👤", "Face Recognition")
        self._face_btn.clicked.connect(
            lambda: self._login_with_method('face')
        )
        auth_panel_layout.addWidget(self._face_btn)

        # Password input (hidden by default)
        self._password_frame = QFrame()
        self._password_frame.setVisible(False)
        self._password_frame.setStyleSheet("QFrame { border: none; background: transparent; }")
        pw_layout = QHBoxLayout(self._password_frame)
        pw_layout.setContentsMargins(0, 0, 0, 0)
        pw_layout.setSpacing(8)

        self._password_input = QLineEdit()
        self._password_input.setPlaceholderText("Enter password...")
        self._password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self._password_input.setFixedHeight(40)
        self._password_input.returnPressed.connect(
            lambda: self._login_with_method('password')
        )
        self._password_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 12px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C['accent']};
            }}
        """)
        pw_layout.addWidget(self._password_input)

        login_btn = QPushButton("Login")
        login_btn.setFixedSize(70, 40)
        login_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        login_btn.clicked.connect(
            lambda: self._login_with_method('password')
        )
        login_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                border: none;
                border-radius: 8px;
                color: #0D1117;
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: #00AACC;
            }}
        """)
        pw_layout.addWidget(login_btn)
        auth_panel_layout.addWidget(self._password_frame)

        main_layout.addWidget(self._auth_panel)
        main_layout.addStretch()

        # ── Footer ─────────────────────────────────────────
        footer = QLabel("Secure voice authentication powered by AI")
        footer.setAlignment(Qt.AlignmentFlag.AlignCenter)
        footer.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 11px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(footer)

    def _load_users(self):
        """Load registered users and create avatar cards"""
        # print("[LOGIN] Loading users...")
        log_info("Loading users for login")

        # Clear existing
        while self._users_layout.count():
            item = self._users_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from backend.security.session_manager import get_session_manager
            session = get_session_manager()
            users = session.get_available_users()

            # print(f"[LOGIN] Found {len(users)} users")

            for user_info in users:
                card = UserAvatarCard(
                    user_info['username'],
                    user_info['is_admin']
                )
                card.clicked.connect(self._on_user_selected)
                self._users_layout.addWidget(card)

            # Add New User card
            add_card = AddUserCard()
            add_card.clicked.connect(self._on_add_user)
            self._users_layout.addWidget(add_card)

        except Exception as e:
            # print(f"[LOGIN] Load users error: {e}")
            log_error(f"Load users error: {e}")

            # Show add user anyway
            add_card = AddUserCard()
            add_card.clicked.connect(self._on_add_user)
            self._users_layout.addWidget(add_card)

    def _start_voice_login(self):
        try:
            # Load all user data HERE on the main thread — never inside the thread
            from backend.utils.utils import list_users, load_profile
            usernames  = list_users()
            users_data = []
            for u in usernames:
                profile = load_profile(u)
                if profile:
                    users_data.append((u, profile))

            if not users_data:
                return

            self._waveform.start()
            self._voice_thread = VoiceLoginThread(users_data, self)  # pass data in
            self._voice_thread.login_success.connect(self._on_voice_login_success)
            self._voice_thread.login_failed.connect(self._on_voice_login_failed)
            self._voice_thread.listening_started.connect(
                lambda: self._voice_status.setText("Listening for voice password...")
            )
            self._voice_thread.start()

        except Exception as e:
            from backend.utils.logger import log_error
            log_error(f"Voice login start error: {e}")

    def _on_user_selected(self, username):
        """Show auth method panel for selected user"""
        # print(f"[LOGIN] User selected: {username}")
        log_info(f"User selected: {username}")
        self._selected_user = username
        self._selected_label.setText(f"Login as: {username}")
        self._password_frame.setVisible(False)
        self._auth_panel.setVisible(True)

        # Show available auth methods
        try:
            from backend.utils.utils import load_profile
            profile = load_profile(username)
            methods = profile.get('auth_methods', [])

            self._voice_btn.setVisible('voice' in methods)
            self._face_btn.setVisible('face' in methods)
            self._password_btn.setVisible('password' in methods)

        except Exception as e:
            # print(f"[LOGIN] Auth method check error: {e}")
            log_error(f"Auth method check: {e}")

    def _show_password_input(self):
        """Show password input field"""
        # print("[LOGIN] Showing password input")
        self._password_frame.setVisible(True)
        self._password_input.setFocus()

    def _login_with_method(self, method):
        """Attempt login in background thread — never on main thread"""
        if not self._selected_user:
            return

        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            # Create auth on main thread first
            auth = get_auth_orchestrator()

            credential = None
            if method == 'password':
                credential = self._password_input.text()
                if not credential:
                    self._password_input.setFocus()
                    return

            self._voice_status.setText("Authenticating...")
            log_info(f"Login attempt: {self._selected_user} via {method}")

            # Run in background thread — faster_whisper cannot run on main thread
            self._auth_thread = LoginAuthThread(
                auth, self._selected_user, method, credential, self
            )
            self._auth_thread.auth_success.connect(self._on_auth_success)
            self._auth_thread.auth_failed.connect(self._on_auth_failed)
            self._auth_thread.start()

        except Exception as e:
            log_error(f"Login error: {e}")
            self._voice_status.setText("Login failed. Try again.")

    def _on_auth_success(self, username, method, profile):
        self._stop_voice_login()
        self.login_success.emit(username, method, profile)

    def _on_auth_failed(self, message):
        self._voice_status.setText(f"❌ {message}")
        log_error(f"Login failed: {message}")

    def _on_voice_login_success(self, username, method):
        """Handle successful voice auto-login"""
        # print(f"[LOGIN] ✅ Voice auto-login: {username}")
        log_info(f"Voice auto-login success: {username}")
        self._waveform.stop()
        self._voice_status.setText(f"Welcome back, {username}! 👋")

        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()
            session = auth.session.create_session(username, method)
            if session:
                QTimer.singleShot(
                    800,
                    lambda: self.login_success.emit(
                        username, method, session.profile
                    )
                )
        except Exception as e:
            # print(f"[LOGIN] Session create error: {e}")
            log_error(f"Session create error: {e}")

    def _on_voice_login_failed(self, error):
        """Handle voice login failure"""
        # print(f"[LOGIN] Voice login failed: {error}")
        self._voice_status.setText("Say your voice password to login")

    def _on_add_user(self):
        """Handle add new user click"""
        # print("[LOGIN] Add user clicked")
        import traceback
        print("=== ADD USER CLICKED ===", flush=True)
        traceback.print_stack()
        log_info("Add new user from login")
        self._stop_voice_login()
        print("=== VOICE LOGIN STOPPED ===", flush=True)
        self.register_requested.emit()
        print("=== SIGNAL EMITTED ===", flush=True)
        
    def _stop_voice_login(self):
        """Stop voice login thread and release microphone before proceeding"""
        # print("[LOGIN] Stopping voice login...")
        if self._voice_thread and self._voice_thread.isRunning():
            self._voice_thread.stop()
            self._voice_thread.quit()
            self._voice_thread.wait(3000)  # wait up to 3s for mic to release
        # Force sounddevice to release mic immediately
        try:
            import sounddevice as sd
            sd.stop()
        except Exception:
            pass
        self._waveform.stop()

    def refresh_users(self):
        """Reload user list"""
        # print("[LOGIN] Refreshing users...")
        self._load_users()

    def closeEvent(self, event):
        """Clean up on close"""
        # print("[LOGIN] Window closing...")
        self._stop_voice_login()
        super().closeEvent(event)