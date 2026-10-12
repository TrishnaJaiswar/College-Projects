# DeskmateAI/ui/views/main_window.py

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QGraphicsDropShadowEffect
)
from PyQt6.QtCore import (
    Qt, QTimer, QThread, pyqtSignal, QPoint,
    QPropertyAnimation, QEasingCurve, QRect
)
from PyQt6.QtGui import (
    QColor, QFont, QPainter, QBrush, QPen,
    QLinearGradient, QScreen, QPixmap
)

# ============================================================
# FLOATING COMMAND WINDOW FOR DESKMATEAI
# Matches Image 2 design exactly
# Small floating window that appears on:
# - Voice command "open dashboard" / "main window"
# - Tray icon left click
# Auto-hides after command execution
# Shows waveform animation when listening
# Shows last command and result
# Always on top, no taskbar entry
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ui.animations.waveform import LargeWaveformWidget
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

# ── Main Floating Window ──────────────────────────────────────

class MainWindow(QWidget):
    """
    Floating command window
    Matches Image 2 design exactly
    Appears on wake word or tray click
    Auto-hides after 5 seconds of inactivity
    """

    close_requested = pyqtSignal()
    open_dashboard = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._auto_hide_timer = QTimer(self)
        self._auto_hide_timer.setSingleShot(True)
        self._auto_hide_timer.timeout.connect(self._auto_hide)
        self._auto_hide_delay = 5000  # 5 seconds

        self._current_status = "idle"
        self._last_command = ""
        self._last_result = ""
        self._last_success = True

        self._setup_window()
        self._setup_ui()

        log_info("MainWindow (floating) initialized")
        # print("[MAIN_WIN] MainWindow initialized")

    def _setup_window(self):
        """Configure floating window properties"""
        self.setWindowTitle("DeskmateAI")
        self.setFixedSize(380, 260)

        # Always on top, no taskbar, frameless
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.FramelessWindowHint
        )

        # Slightly transparent background
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setStyleSheet("background: transparent;")

        # Position at top center of screen
        self._position_window()

    def _position_window(self):
        """Position window at top center of screen"""
        try:
            from PyQt6.QtWidgets import QApplication
            screen = QApplication.primaryScreen()
            if screen:
                screen_rect = screen.availableGeometry()
                x = screen_rect.center().x() - self.width() // 2
                y = screen_rect.top() + 60
                self.move(x, y)
                # print(f"[MAIN_WIN] Positioned at ({x}, {y})")
        except Exception as e:
            # print(f"[MAIN_WIN] Position error: {e}")
            log_error(f"Window position error: {e}")

    def _setup_ui(self):
        """Build UI matching Image 2"""

        # ── Main container with rounded corners ────────────
        container = QFrame(self)
        container.setFixedSize(380, 260)
        container.setStyleSheet(f"""
            QFrame {{
                background-color: {C['bg']};
                border: 1px solid {C['border']};
                border-radius: 14px;
            }}
        """)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        container.setGraphicsEffect(shadow)

        main_layout = QVBoxLayout(container)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Top Bar ────────────────────────────────────────
        top_bar = QFrame()
        top_bar.setFixedHeight(44)
        top_bar.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border-bottom: 1px solid {C['border']};
                border-top-left-radius: 14px;
                border-top-right-radius: 14px;
                border-bottom-left-radius: 0;
                border-bottom-right-radius: 0;
            }}
        """)

        top_bar_layout = QHBoxLayout(top_bar)
        top_bar_layout.setContentsMargins(14, 0, 14, 0)
        top_bar_layout.setSpacing(8)

        # Mic icon
        mic_icon = QLabel("🎙")
        mic_icon.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                font-size: 16px;
            }
        """)
        top_bar_layout.addWidget(mic_icon)

        # Title
        title = QLabel("DeskmateAI")
        title.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 14px;
                font-weight: bold;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        top_bar_layout.addWidget(title)
        top_bar_layout.addStretch()

        # Close button
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(24, 24)
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self.hide_window)
        close_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                color: {C['subtext']};
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
            QPushButton:hover {{
                color: {C['error']};
            }}
        """)
        top_bar_layout.addWidget(close_btn)

        main_layout.addWidget(top_bar)

        # ── Content Area ───────────────────────────────────
        content = QWidget()
        content.setStyleSheet(f"""
            QWidget {{
                background-color: {C['bg']};
                border: none;
            }}
        """)
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(10)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Waveform
        self._waveform = LargeWaveformWidget()
        self._waveform.setFixedSize(200, 70)
        content_layout.addWidget(
            self._waveform,
            0, Qt.AlignmentFlag.AlignCenter
        )

        # Status text — "LISTENING..." in cyan
        self._status_label = QLabel("LISTENING...")
        self._status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {C['accent']};
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
                letter-spacing: 2px;
                background: transparent;
                border: none;
            }}
        """)
        content_layout.addWidget(self._status_label)

        # Last command (quoted)
        self._command_label = QLabel("")
        self._command_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._command_label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        content_layout.addWidget(self._command_label)

        # Result label
        self._result_label = QLabel("")
        self._result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._result_label.setStyleSheet(f"""
            QLabel {{
                color: {C['success']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        content_layout.addWidget(self._result_label)

        main_layout.addWidget(content)

    # ── State Updates ─────────────────────────────────────────

    def set_status(self, status):
        """
        Update display status
        status: idle/listening/processing/executing/success/error
        """
        # print(f"[MAIN_WIN] Status: {status}")
        self._current_status = status

        status_map = {
            "idle":       ("IDLE", C['subtext']),
            "listening":  ("LISTENING...", C['accent']),
            "processing": ("PROCESSING...", C['warning'] if hasattr(self, '_warn') else "#D29922"),
            "executing":  ("EXECUTING...", "#D29922"),
            "success":    ("DONE ✓", C['success']),
            "error":      ("ERROR", C['error']),
            "wakeword":   ("WAKE WORD DETECTED", C['accent']),
        }

        text, color = status_map.get(status, ("IDLE", C['subtext']))
        self._status_label.setText(text)
        self._status_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
                letter-spacing: 2px;
                background: transparent;
                border: none;
            }}
        """)

        # Waveform control
        if status in ["listening", "wakeword"]:
            self._waveform.start()
        elif status in ["idle", "success", "error"]:
            self._waveform.stop()

    def set_transcription(self, text):
        """Show transcribed command text"""
        # print(f"[MAIN_WIN] Command: {text}")
        if text:
            self._command_label.setText(f'"{text}"')
        else:
            self._command_label.setText("")

    def set_result(self, text, success=True):
        """Show command result"""
        # print(f"[MAIN_WIN] Result: {text} | success={success}")
        color = C['success'] if success else C['error']
        icon = "✅" if success else "❌"
        self._result_label.setText(f"{icon} {text}")
        self._result_label.setStyleSheet(f"""
            QLabel {{
                color: {color};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)

    def set_audio_level(self, level):
        """Update waveform with real audio level"""
        self._waveform.set_level(level)

    # ── Window Control ────────────────────────────────────────

    def show_window(self):
        """Show floating window"""
        # print("[MAIN_WIN] Showing window")
        log_info("Floating window shown")
        self._position_window()
        self.show()
        self.raise_()
        self.activateWindow()
        self._reset_auto_hide()

    def hide_window(self):
        """Hide floating window"""
        # print("[MAIN_WIN] Hiding window")
        log_info("Floating window hidden")
        self._auto_hide_timer.stop()
        self._waveform.stop()
        self.hide()

    def _auto_hide(self):
        """Auto hide after inactivity"""
        # print("[MAIN_WIN] Auto-hiding...")
        if self._current_status in ["idle", "success", "error"]:
            self.hide_window()

    def _reset_auto_hide(self):
        """Reset auto hide timer"""
        self._auto_hide_timer.stop()
        self._auto_hide_timer.start(self._auto_hide_delay)

    def on_command_complete(self, intent, success, entity):
        """Called when command execution is complete"""
        # print(f"[MAIN_WIN] Command complete: {intent} | success={success}")
        self.set_status("success" if success else "error")

        result_text = f"{intent.replace('_', ' ').title()}"
        if entity:
            result_text += f": {entity}"
        self.set_result(result_text, success)

        # Auto hide after 3 seconds
        self._auto_hide_timer.stop()
        self._auto_hide_timer.start(3000)

    def clear(self):
        """Clear all displayed info"""
        # print("[MAIN_WIN] Clearing display")
        self._command_label.setText("")
        self._result_label.setText("")
        self.set_status("idle")

    # ── Drag to move ──────────────────────────────────────────

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self._drag_pos = event.globalPosition().toPoint() - self.pos()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            if hasattr(self, '_drag_pos'):
                self.move(event.globalPosition().toPoint() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        if hasattr(self, '_drag_pos'):
            del self._drag_pos