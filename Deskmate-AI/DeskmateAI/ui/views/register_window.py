# DeskmateAI/ui/views/register_window.py

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QFrame, QComboBox,
    QProgressBar, QStackedWidget, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal, QPropertyAnimation
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen, QPixmap
from PyQt6.QtWidgets import QApplication

# ============================================================
# REGISTRATION WINDOW FOR DESKMATEAI
# Matches Image 5 design exactly
# 4 step registration:
# Step 1: Basic Info (username, password, language, wake word)
# Step 2: Face Registration (camera capture)
# Step 3: Voice Password (record passphrase)
# Step 4: Speaker Profile (record voice samples)
# Progress dots at top like Image 5
# Continue button at bottom
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ui.animations.waveform import SmallWaveformWidget
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

# ── Registration Thread ───────────────────────────────────────

class RegistrationThread(QThread):
    """Background thread for registration steps"""
    progress = pyqtSignal(int, int, str)  # step, total, message
    success = pyqtSignal(str)             # success message
    failed = pyqtSignal(str)              # error message

    def __init__(self, step, username, data=None, parent=None):
        super().__init__(parent)
        self.step = step
        self.username = username
        self.data = data or {}
        # print(f"[REG_THREAD] Init: step={step}")

    def run(self):
        # Set OMP/MKL env vars before any torch/numpy load in this thread
        import os
        os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
        os.environ['OMP_NUM_THREADS'] = '1'
        os.environ['OPENBLAS_NUM_THREADS'] = '1'
        os.environ['MKL_NUM_THREADS'] = '1'

        # print(f"[REG_THREAD] Running step: {self.step}")
        try:
            from backend.security.registration import get_registration_manager
            reg = get_registration_manager()

            def progress_cb(current, total, message):
                self.progress.emit(current, total, message)

            if self.step == "face":
                success, message = reg.register_face(
                    self.username,
                    progress_callback=progress_cb
                )
            elif self.step == "voice_password":
                success, message = reg.register_voice_password(
                    self.username,
                    self.data.get('passphrase', 'hey deskmate'),
                    progress_callback=progress_cb
                )
            elif self.step == "speaker":
                success, message = reg.register_speaker_profile(
                    self.username,
                    progress_callback=progress_cb
                )
            else:
                success, message = False, "Unknown step"

            if success:
                # print(f"[REG_THREAD] ✅ Step success: {self.step}")
                self.success.emit(message)
            else:
                # print(f"[REG_THREAD] ❌ Step failed: {message}")
                self.failed.emit(message)

        except Exception as e:
            # print(f"[REG_THREAD] Error: {e}")
            log_error(f"Registration thread error: {e}")
            self.failed.emit(str(e))


# ── Step Progress Bar ─────────────────────────────────────────

class StepProgressBar(QWidget):
    """
    4-step progress indicator
    Matches Image 5 exactly:
    Filled cyan dot → lines → empty dots
    Labels below: Basic Info, Face, Voice, Speaker
    """

    STEPS = ["Basic Info", "Face", "Voice", "Speaker"]

    def __init__(self, parent=None):
        super().__init__(parent)
        self._current_step = 0
        self.setFixedHeight(60)
        self._setup_ui()
        # print("[STEP_BAR] Initialized")

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 0, 10, 0)
        layout.setSpacing(0)

        self._dots = []
        self._labels = []

        for i, step_name in enumerate(self.STEPS):
            # Step container
            step_widget = QWidget()
            step_layout = QVBoxLayout(step_widget)
            step_layout.setContentsMargins(0, 0, 0, 0)
            step_layout.setSpacing(4)
            step_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

            # Dot
            dot = QLabel()
            dot.setFixedSize(20, 20)
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._update_dot(dot, i == 0)
            self._dots.append(dot)
            step_layout.addWidget(dot, 0, Qt.AlignmentFlag.AlignCenter)

            # Label
            label = QLabel(step_name)
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            self._update_label(label, i == 0)
            self._labels.append(label)
            step_layout.addWidget(label, 0, Qt.AlignmentFlag.AlignCenter)

            layout.addWidget(step_widget)

            # Connector line (between steps)
            if i < len(self.STEPS) - 1:
                line = QFrame()
                line.setFrameShape(QFrame.Shape.HLine)
                line.setFixedHeight(2)
                line.setStyleSheet(f"background-color: {C['border']}; border: none;")
                line.setSizePolicy(
                    QSizePolicy.Policy.Expanding,
                    QSizePolicy.Policy.Fixed
                )
                # Align line with dots vertically
                line_wrapper = QWidget()
                line_wrapper_layout = QVBoxLayout(line_wrapper)
                line_wrapper_layout.setContentsMargins(0, 0, 0, 16)
                line_wrapper_layout.addWidget(line)
                layout.addWidget(line_wrapper)

    def _update_dot(self, dot, active):
        if active:
            dot.setStyleSheet(f"""
                QLabel {{
                    background-color: {C['accent']};
                    border-radius: 10px;
                    border: none;
                }}
            """)
        else:
            dot.setStyleSheet(f"""
                QLabel {{
                    background-color: transparent;
                    border: 2px solid {C['border']};
                    border-radius: 10px;
                }}
            """)

    def _update_label(self, label, active):
        color = C['accent'] if active else C['subtext']
        label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 11px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)

    def set_step(self, step):
        """Update current step (0-3)"""
        # print(f"[STEP_BAR] Step: {step}")
        self._current_step = step
        for i, (dot, label) in enumerate(zip(self._dots, self._labels)):
            self._update_dot(dot, i <= step)
            self._update_label(label, i == step)


# ── Input Field ───────────────────────────────────────────────

class InputField(QWidget):
    """Styled input field with label"""

    def __init__(self, label_text, placeholder, password=False, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        # Label
        label = QLabel(label_text)
        label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(label)

        # Input
        self.input = QLineEdit()
        self.input.setPlaceholderText(placeholder)
        self.input.setFixedHeight(46)
        if password:
            self.input.setEchoMode(QLineEdit.EchoMode.Password)
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 10px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C['accent']};
            }}
            QLineEdit::placeholder {{
                color: {C['subtext']};
            }}
        """)
        layout.addWidget(self.input)

    def text(self):
        return self.input.text()

    def set_error(self, error_text):
        self.input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['error']};
                border-radius: 10px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 14px;
            }}
        """)


# ── Step 1: Basic Info ────────────────────────────────────────

class BasicInfoStep(QWidget):
    """Step 1 - matches Image 5 exactly"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        # Username
        self.username_field = InputField(
            "Username", "Enter username"
        )
        layout.addWidget(self.username_field)

        # Password
        self.password_field = InputField(
            "Password", "Enter password", password=True
        )
        layout.addWidget(self.password_field)

        # Confirm Password
        self.confirm_field = InputField(
            "Confirm Password", "Confirm password", password=True
        )
        layout.addWidget(self.confirm_field)

        # Language
        lang_label = QLabel("Language")
        lang_label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(lang_label)

        self.language_combo = QComboBox()
        self.language_combo.addItems(["English", "Hindi", "Marathi", "Hinglish (Hindi+English)", "Minglish (Marathi+English)"])
        self.language_combo.setFixedHeight(46)
        self.language_combo.setStyleSheet(f"""
            QComboBox {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 10px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 14px;
            }}
            QComboBox:focus {{
                border: 1px solid {C['accent']};
            }}
            QComboBox::drop-down {{
                border: none;
                padding-right: 10px;
            }}
            QComboBox::down-arrow {{
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid {C['subtext']};
                margin-right: 10px;
            }}
            QComboBox QAbstractItemView {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                color: {C['text']};
                selection-background-color: {C['surface']};
            }}
        """)
        layout.addWidget(self.language_combo)

        # Wake Word
        self.wake_word_field = InputField(
            "Wake Word", "e.g., Hey Deskmate"
        )
        self.wake_word_field.input.setText("hey deskmate")
        layout.addWidget(self.wake_word_field)

        layout.addStretch()

    def get_data(self):
        lang_map = {
            "English": ("en", "English"),
            "Hindi": ("hi", "Hindi"),
            "Marathi": ("mr", "Marathi"),
            "Hinglish (Hindi+English)": ("hinglish", "Hinglish"),
            "Minglish (Marathi+English)": ("minglish", "Minglish"),
        }
        lang_text = self.language_combo.currentText()
        lang_code, lang_name = lang_map[lang_text]

        return {
            "username": self.username_field.text().strip(),
            "password": self.password_field.text(),
            "confirm_password": self.confirm_field.text(),
            "language_code": lang_code,
            "language_name": lang_name,
            "wake_word": self.wake_word_field.text().strip() or "hey deskmate"
        }


# ── Step 2: Face Registration ─────────────────────────────────

class FaceStep(QWidget):
    """Step 2 - Face registration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._cap = None
        self._camera_timer = QTimer()
        self._camera_timer.timeout.connect(self._update_frame)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Camera preview area
        self._camera_label = QLabel()
        self._camera_label.setFixedSize(220, 165)
        self._camera_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._camera_label.setStyleSheet(f"""
            QLabel {{
                background-color: {C['surface2']};
                border: 2px solid {C['border']};
                border-radius: 12px;
                color: {C['subtext']};
                font-size: 13px;
            }}
        """)
        self._camera_label.setText("📷\nStarting camera...")
        layout.addWidget(self._camera_label, 0, Qt.AlignmentFlag.AlignCenter)

        # Start camera automatically
        QTimer.singleShot(500, self._start_camera)

        # Instructions
        self._instruction = QLabel("Position your face in the camera")
        self._instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction.setWordWrap(True)
        self._instruction.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self._instruction)

        # Progress
        self._progress_label = QLabel("0 / 3 samples captured")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self._progress_label)

        # Skip button
        self._skip_btn = QPushButton("⚠️ Required — Cannot Skip")
        self._skip_btn.setFixedHeight(36)
        self._skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                border-color: {C['accent']};
                color: {C['accent']};
            }}
        """)
        layout.addWidget(self._skip_btn)
        layout.addStretch()

    def _start_camera(self):
        """Start camera feed"""
        try:
            import cv2
            self._cap = cv2.VideoCapture(0)
            if self._cap.isOpened():
                self._camera_timer.start(33)  # ~30 FPS
                # print("[FACE_STEP] Camera started")
            else:
                self._camera_label.setText("❌\nCamera not found")
        except Exception as e:
            self._camera_label.setText(f"❌\nCamera error:\n{str(e)[:30]}")

    def _update_frame(self):
        """Update camera preview frame"""
        try:
            import cv2
            from PyQt6.QtGui import QImage, QPixmap

            if self._cap and self._cap.isOpened():
                ret, frame = self._cap.read()
                if ret:
                    # Convert BGR to RGB
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Resize to fit label
                    frame = cv2.resize(frame, (220, 165))

                    # Convert to QPixmap
                    h, w, ch = frame.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(
                        frame.data,
                        w, h,
                        bytes_per_line,
                        QImage.Format.Format_RGB888
                    )
                    pixmap = QPixmap.fromImage(qt_image)
                    self._camera_label.setPixmap(pixmap)
                    self._camera_label.setStyleSheet(f"""
                        QLabel {{
                            background-color: {C['surface2']};
                            border: 2px solid {C['accent']};
                            border-radius: 12px;
                        }}
                    """)
        except Exception as e:
            pass

    def stop_camera(self):
        """Stop camera feed"""
        self._camera_timer.stop()
        if self._cap:
            self._cap.release()
            self._cap = None
        # print("[FACE_STEP] Camera stopped")

    def showEvent(self, event):
        """Start camera when step shown"""
        super().showEvent(event)
        QTimer.singleShot(300, self._start_camera)

    def hideEvent(self, event):
        """Stop camera when step hidden"""
        super().hideEvent(event)
        self.stop_camera()

    def set_progress(self, current, total, message):
        self._progress_label.setText(f"{current} / {total} samples captured")
        self._instruction.setText(message)

    def set_instruction(self, text):
        self._instruction.setText(text)

    def get_skip_button(self):
        return self._skip_btn


# ── Step 3: Voice Password ────────────────────────────────────

class VoicePasswordStep(QWidget):
    """Step 3 - Voice password registration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Passphrase input
        phrase_label = QLabel("Your Voice Passphrase")
        phrase_label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(phrase_label)

        self._passphrase_input = QLineEdit()
        self._passphrase_input.setPlaceholderText("e.g., hey deskmate activate")
        self._passphrase_input.setFixedHeight(46)
        self._passphrase_input.setText("hey deskmate")
        self._passphrase_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 10px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 14px;
            }}
            QLineEdit:focus {{
                border: 1px solid {C['accent']};
            }}
        """)
        layout.addWidget(self._passphrase_input)

        # Waveform
        self._waveform = SmallWaveformWidget()
        layout.addWidget(self._waveform, 0, Qt.AlignmentFlag.AlignCenter)

        # Instruction
        self._instruction = QLabel("Say your passphrase when ready")
        self._instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction.setWordWrap(True)
        self._instruction.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self._instruction)

        # Progress
        self._progress_label = QLabel("0 / 3 recordings")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self._progress_label)

        # Skip
        self._skip_btn = QPushButton("⚠️ Required — Cannot Skip")
        self._skip_btn.setFixedHeight(36)
        self._skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                border-color: {C['accent']};
                color: {C['accent']};
            }}
        """)
        layout.addWidget(self._skip_btn)
        layout.addStretch()

    def get_passphrase(self):
        return self._passphrase_input.text().strip() or "hey deskmate"

    def set_progress(self, current, total, message):
        self._progress_label.setText(f"{current} / {total} recordings")
        self._instruction.setText(message)
        self._waveform.start()

    def get_skip_button(self):
        return self._skip_btn


# ── Step 4: Speaker Profile ───────────────────────────────────

class SpeakerStep(QWidget):
    """Step 4 - Speaker profile registration"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Waveform
        self._waveform = SmallWaveformWidget()
        layout.addWidget(self._waveform, 0, Qt.AlignmentFlag.AlignCenter)

        # Instruction
        self._instruction = QLabel(
            "Speak freely for 5 seconds\nso we can learn your voice"
        )
        self._instruction.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._instruction.setWordWrap(True)
        self._instruction.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
                line-height: 1.5;
            }}
        """)
        layout.addWidget(self._instruction)

        # Progress
        self._progress_label = QLabel("0 / 3 voice samples")
        self._progress_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._progress_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self._progress_label)

        # Skip
        self._skip_btn = QPushButton("⚠️ Required — Cannot Skip")
        self._skip_btn.setFixedHeight(36)
        self._skip_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._skip_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                border-color: {C['accent']};
                color: {C['accent']};
            }}
        """)
        layout.addWidget(self._skip_btn)
        layout.addStretch()

    def set_progress(self, current, total, message):
        self._progress_label.setText(f"{current} / {total} voice samples")
        self._instruction.setText(message)
        if current > 0:
            self._waveform.start()

    def get_skip_button(self):
        return self._skip_btn


# ── Register Window ───────────────────────────────────────────

class RegisterWindow(QWidget):
    """
    Main registration window
    Matches Image 5 design exactly
    4 step wizard with progress dots
    """

    registration_complete = pyqtSignal(str)  # username
    back_to_login = pyqtSignal()

    def __init__(self, admin_mode=False, parent=None):
        super().__init__(parent)
        self._admin_mode = admin_mode
        self._current_step = 0
        self._username = None
        self._reg_thread = None
        self._completed_steps = {
            "basic_info": False,
            "face": False,
            "voice": False,
            "speaker": False
        }

        self._setup_window()
        self._setup_ui()

        log_info("RegisterWindow initialized")
        # print("[REGISTER] RegisterWindow initialized")

    def _setup_window(self):
        self.setWindowTitle("DeskmateAI - New User Registration")
        self.setFixedSize(500, 660)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; }}")

    def _setup_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 20, 30, 0)
        main_layout.setSpacing(0)

        # ── Header ─────────────────────────────────────────
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(0, 0, 0, 0)

        # Back button
        self._back_btn = QPushButton("←")
        self._back_btn.setFixedSize(32, 32)
        self._back_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._back_btn.clicked.connect(self._go_back)
        self._back_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {C['text']};
                font-size: 18px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                color: {C['accent']};
            }}
        """)
        header_layout.addWidget(self._back_btn)
        header_layout.addSpacing(8)

        # Title
        title = QLabel("New User Registration")
        title.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        main_layout.addLayout(header_layout)
        main_layout.addSpacing(16)

        # ── Step Progress Bar ──────────────────────────────
        self._step_bar = StepProgressBar()
        main_layout.addWidget(self._step_bar)
        main_layout.addSpacing(20)

        # ── Error Label ────────────────────────────────────
        self._error_label = QLabel("")
        self._error_label.setVisible(False)
        self._error_label.setWordWrap(True)
        self._error_label.setStyleSheet(f"""
            QLabel {{
                color: {C['error']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background-color: #1A0D0D;
                border: 1px solid {C['error']};
                border-radius: 6px;
                padding: 8px;
            }}
        """)
        main_layout.addWidget(self._error_label)

        # ── Step Content ───────────────────────────────────
        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: transparent; }")

        # Create steps
        self._step1 = BasicInfoStep()
        self._step2 = FaceStep()
        self._step3 = VoicePasswordStep()
        self._step4 = SpeakerStep()

        self._stack.addWidget(self._step1)
        self._stack.addWidget(self._step2)
        self._stack.addWidget(self._step3)
        self._stack.addWidget(self._step4)

        main_layout.addWidget(self._stack)
        main_layout.addStretch()

        # ── Status Label ───────────────────────────────────
        self._status_label = QLabel("")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        main_layout.addWidget(self._status_label)
        main_layout.addSpacing(12)

        # ── Continue Button ────────────────────────────────
        self._continue_btn = QPushButton("Continue  →")
        self._continue_btn.setFixedHeight(52)
        self._continue_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._continue_btn.clicked.connect(self._on_continue)
        self._update_continue_btn("Continue  →")
        main_layout.addWidget(self._continue_btn)
        main_layout.addSpacing(16)

        # Skip buttons show warning — all steps required
        self._step2.get_skip_button().clicked.connect(
            lambda: self._show_skip_warning("Face")
        )
        self._step3.get_skip_button().clicked.connect(
            lambda: self._show_skip_warning("Voice Password")
        )
        self._step4.get_skip_button().clicked.connect(
            lambda: self._show_skip_warning("Speaker Profile")
        )

    def _update_continue_btn(self, text):
        self._continue_btn.setText(text)
        self._continue_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                border: none;
                border-radius: 10px;
                color: #0D1117;
                font-size: 15px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                background-color: #00AACC;
            }}
            QPushButton:pressed {{
                background-color: #007799;
            }}
            QPushButton:disabled {{
                background-color: {C['border']};
                color: {C['subtext']};
            }}
        """)

    def _go_back(self):
        """Go back to login or previous step"""
        # print(f"[REGISTER] Back: step={self._current_step}")
        if self._current_step == 0:
            self.back_to_login.emit()
        else:
            self._current_step -= 1
            self._stack.setCurrentIndex(self._current_step)
            self._step_bar.set_step(self._current_step)
            self._update_continue_btn("Continue  →")

    def _show_error(self, message):
        """Show error message"""
        self._error_label.setText(f"❌  {message}")
        self._error_label.setVisible(True)
        QTimer.singleShot(4000, lambda: self._error_label.setVisible(False))

    def _show_status(self, message):
        """Show status message"""
        self._status_label.setText(message)

    def _on_continue(self):
        """Handle continue button"""
        # print(f"[REGISTER] Continue: step={self._current_step}")

        if self._current_step == 0:
            self._process_step1()
        elif self._current_step == 1:
            self._process_step2()
        elif self._current_step == 2:
            self._process_step3()
        elif self._current_step == 3:
            self._process_step4()

    def _process_step1(self):
        """Process basic info step"""
        # print("[REGISTER] Processing step 1...")
        data = self._step1.get_data()

        if not data['username']:
            self._show_error("Username is required")
            return
        if not data['password']:
            self._show_error("Password is required")
            return
        if data['password'] != data['confirm_password']:
            self._show_error("Passwords do not match")
            return

        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()

            success, message = auth.start_registration(
                username=data['username'],
                password=data['password'],
                confirm_password=data['confirm_password'],
                language_code=data['language_code'],
                language_name=data['language_name'],
                wake_word=data['wake_word']
            )

            if success:
                self._username = data['username']
                self._completed_steps['basic_info'] = True
                log_info(f"Step 1 complete: {self._username}")
                self._advance_step()
            else:
                self._show_error(message)

        except Exception as e:
            # print(f"[REGISTER] Step 1 error: {e}")
            log_error(f"Step 1 error: {e}")
            self._show_error(str(e))

    def _process_step2(self):
        """Process face registration"""
        if not self._username:
            self._show_error("Please complete step 1 first")
            return

        self._continue_btn.setEnabled(False)
        self._show_status("📷 Capturing face samples...")

        if self._reg_thread and self._reg_thread.isRunning():
            self._reg_thread.quit()
            self._reg_thread.wait(2000)

        self._reg_thread = RegistrationThread(
            "face", self._username
        )
        self._reg_thread.progress.connect(
            lambda c, t, m: self._step2.set_progress(c, t, m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.success.connect(
            lambda m: self._on_step_success(m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.failed.connect(
            lambda m: self._on_step_failed(m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.start()

    def _process_step3(self):
        """Process voice password registration"""
        if not self._username:
            return

         # 🔥 ADD THIS BLOCK HERE
        from PyQt6.QtWidgets import QApplication
        app = QApplication.instance()
        controller = getattr(app, "controller", None)

        if controller:
            controller.stop_audio_stream()
        passphrase = self._step3.get_passphrase()
        if not passphrase:
            self._show_error("Please enter a passphrase")
            return

        self._continue_btn.setEnabled(False)
        self._show_status("🎤 Recording voice password... Please speak now")

        # Stop any existing thread
        if self._reg_thread and self._reg_thread.isRunning():
            self._reg_thread.quit()
            self._reg_thread.wait(2000)

        self._reg_thread = RegistrationThread(
            "voice_password", self._username,
            data={'passphrase': passphrase}
        )
        self._reg_thread.progress.connect(
            lambda c, t, m: self._step3.set_progress(c, t, m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.success.connect(
            lambda m: self._on_step_success(m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.failed.connect(
            lambda m: self._on_step_failed(m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.start()
        
    def _process_step4(self):
        """Process speaker profile registration"""
        if not self._username:
            return

        self._continue_btn.setEnabled(False)
        self._show_status("🎤 Recording speaker profile... Please speak freely")

        if self._reg_thread and self._reg_thread.isRunning():
            self._reg_thread.quit()
            self._reg_thread.wait(2000)

        self._reg_thread = RegistrationThread(
            "speaker", self._username
        )
        self._reg_thread.progress.connect(
            lambda c, t, m: self._step4.set_progress(c, t, m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.success.connect(
            lambda m: self._on_step_success(m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.failed.connect(
            lambda m: self._on_step_failed(m),
            Qt.ConnectionType.QueuedConnection
        )
        self._reg_thread.start()
        

    def _on_step_success(self, message):
        """Handle step completion"""
        self._continue_btn.setEnabled(True)
        self._show_status(f"✅ {message}")

        # Mark current step complete
        step_keys = ["basic_info", "face", "voice", "speaker"]
        if self._current_step < len(step_keys):
            self._completed_steps[step_keys[self._current_step]] = True
            # print(f"[REGISTER] Step complete: {step_keys[self._current_step]}")

        # 🔥 Restart audio worker AFTER voice step
        if self._current_step == 2:
            from PyQt6.QtWidgets import QApplication
            app = QApplication.instance()
            controller = getattr(app, "controller", None)
            if controller:
                print("[FIX] Restarting audio worker after recording...")
                controller._start_audio_worker()
        QTimer.singleShot(800, self._advance_step)

    def _on_step_failed(self, message):
        """Handle step failure"""
        # print(f"[REGISTER] Step failed: {message}")
        self._continue_btn.setEnabled(True)
        self._show_error(message)
        self._show_status("")
    
    def _show_skip_warning(self, step_name):
        """Show warning that all steps are required"""
        self._show_error(
            f"⚠️ {step_name} registration is required.\n"
            f"All steps must be completed to register."
        )
        # print(f"[REGISTER] Skip attempted: {step_name}")

    def _advance_step(self):
        """Move to next step"""
        # print(f"[REGISTER] Advancing from step {self._current_step}")
        self._current_step += 1
        # Stop camera if leaving face step
        if self._current_step == 2:
            self._step2.stop_camera()
            
        if self._current_step >= 4:
            self._complete_registration()
            return

        self._stack.setCurrentIndex(self._current_step)
        self._step_bar.set_step(self._current_step)
        self._show_status("")

        if self._current_step == 3:
            self._update_continue_btn("Complete Registration ✓")

    def _complete_registration(self):
        """Complete registration — only if ALL steps done"""
        # print(f"[REGISTER] Checking completion: {self._completed_steps}")

        # Check all steps completed
        incomplete = [
            step for step, done
            in self._completed_steps.items()
            if not done
        ]

        if incomplete:
            # Format step names nicely
            step_names = {
                "basic_info": "Basic Info",
                "face":       "Face Registration",
                "voice":      "Voice Password",
                "speaker":    "Speaker Profile"
            }
            missing = [step_names[s] for s in incomplete]
            self._show_error(
                f"Please complete: {', '.join(missing)}"
            )
            # print(f"[REGISTER] Incomplete steps: {missing}")
            log_warning(f"Registration incomplete: {missing}")
            return

        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()
            success, message = auth.complete_registration(self._username)

            if success:
                log_info(f"Registration complete: {self._username}")
                # print(f"[REGISTER] ✅ Complete: {self._username}")
                self.registration_complete.emit(self._username)
            else:
                self._show_error(f"Registration failed: {message}")
                log_error(f"Registration failed: {message}")

        except Exception as e:
            log_error(f"Complete registration error: {e}")
            # Still emit to avoid getting stuck
            self.registration_complete.emit(self._username or "")