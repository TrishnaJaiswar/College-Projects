# DeskmateAI/ui/views/dashboard_window.py

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QScrollArea, QGridLayout,
    QSizePolicy, QSpacerItem
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread
from PyQt6.QtGui import QColor, QFont, QPainter, QBrush, QPen

# ============================================================
# DASHBOARD WINDOW FOR DESKMATEAI
# Matches Image 3 design exactly
# Shows:
# - Header with username + active dot
# - Recent commands list (last 5)
# - System status grid (Mic, SBERT, Ollama, Wake Word)
# - Footer buttons (Settings, Logout, Exit)
# Opens from tray icon left click
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

from ui.animations.status_indicator import StatusCard, GlowDot
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
    "warning":  "#D29922",
}

# ── Command Row Widget ────────────────────────────────────────

class CommandRow(QWidget):
    """
    Single command row in recent commands list
    Matches Image 3 command rows exactly:
    command text | intent tag | checkmark | time
    """

    def __init__(self, command, intent, success, time_str, parent=None):
        super().__init__(parent)
        self.setFixedHeight(46)
        self.setStyleSheet(f"""
            QWidget {{
                background-color: transparent;
                border: none;
            }}
            QWidget:hover {{
                background-color: {C['surface2']};
                border-radius: 6px;
            }}
        """)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 0, 12, 0)
        layout.setSpacing(8)

        # Command text
        cmd_label = QLabel(command)
        cmd_label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        cmd_label.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Preferred
        )
        layout.addWidget(cmd_label)

        # Intent tag
        intent_tag = QLabel(intent)
        intent_tag.setFixedHeight(22)
        intent_tag.setContentsMargins(8, 2, 8, 2)
        intent_tag.setStyleSheet(f"""
            QLabel {{
                background-color: {C['surface2']};
                border: 1px solid {C['accent']};
                border-radius: 4px;
                color: {C['accent']};
                font-size: 11px;
                font-family: 'Segoe UI';
            }}
        """)
        layout.addWidget(intent_tag)

        # Success/fail icon
        icon = "✓" if success else "✗"
        icon_color = C['success'] if success else C['error']
        status_icon = QLabel(icon)
        status_icon.setFixedWidth(20)
        status_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        status_icon.setStyleSheet(f"""
            QLabel {{
                color: {icon_color};
                font-size: 14px;
                font-weight: bold;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(status_icon)

        # Time
        time_label = QLabel(time_str)
        time_label.setFixedWidth(65)
        time_label.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        time_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 11px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(time_label)


# ── Section Title ─────────────────────────────────────────────

class SectionTitle(QLabel):
    """Section header label matching Image 3"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 11px;
                font-weight: bold;
                font-family: 'Segoe UI';
                letter-spacing: 1px;
                background: transparent;
                border: none;
            }}
        """)
        self.setFixedHeight(24)


# ── Footer Button ─────────────────────────────────────────────

class FooterButton(QPushButton):
    """Footer action button"""

    def __init__(self, icon, text, danger=False, parent=None):
        super().__init__(f"{icon} {text}", parent)
        self.setFixedHeight(36)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if danger:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['surface2']};
                    border: 1px solid {C['border']};
                    border-radius: 8px;
                    color: {C['error']};
                    font-size: 13px;
                    font-family: 'Segoe UI';
                    padding: 0 14px;
                }}
                QPushButton:hover {{
                    background-color: #1A0D0D;
                    border-color: {C['error']};
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['surface2']};
                    border: 1px solid {C['border']};
                    border-radius: 8px;
                    color: {C['text']};
                    font-size: 13px;
                    font-family: 'Segoe UI';
                    padding: 0 14px;
                }}
                QPushButton:hover {{
                    background-color: {C['surface']};
                    border-color: {C['accent']};
                    color: {C['accent']};
                }}
            """)


# ── System Status Checker Thread ──────────────────────────────

class SystemStatusThread(QThread):
    """Background thread to check system component status"""
    status_ready = pyqtSignal(dict)

    def run(self):
        # print("[STATUS_THREAD] Checking system status...")
        status = {
            "microphone": "inactive",
            "sbert":      "inactive",
            "ollama":     "inactive",
            "wake_word":  "inactive",
        }

        try:
            # Check microphone
            import sounddevice as sd
            devices = sd.query_devices(kind='input')
            if devices:
                status["microphone"] = "success"
        except:
            status["microphone"] = "error"

        try:
            # Check SBERT
            from NLP.nlp.sbert_engine import get_sbert_engine
            sbert = get_sbert_engine()
            if sbert.is_loaded() if hasattr(sbert, 'is_loaded') else sbert._model_loaded:
                status["sbert"] = "success"
            else:
                status["sbert"] = "warning"
        except:
            status["sbert"] = "warning"

        try:
            # Check Ollama
            import requests
            response = requests.get(
                "http://localhost:11434/api/tags",
                timeout=2
            )
            if response.status_code == 200:
                status["ollama"] = "success"
            else:
                status["ollama"] = "error"
        except:
            status["ollama"] = "inactive"

        # Wake word always active if pipeline running
        status["wake_word"] = "active"

        # print(f"[STATUS_THREAD] Status: {status}")
        self.status_ready.emit(status)


# ── Dashboard Window ──────────────────────────────────────────

class DashboardWindow(QWidget):
    """
    Main dashboard window
    Matches Image 3 design exactly
    """

    settings_requested = pyqtSignal()
    logout_requested = pyqtSignal()
    exit_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self._username = "User"
        self._is_admin = False
        self._command_history = []
        self._status_thread = None

        self._setup_window()
        self._setup_ui()

        # Refresh status every 30 seconds
        self._status_timer = QTimer(self)
        self._status_timer.timeout.connect(self._refresh_status)
        self._status_timer.start(30000)

        log_info("DashboardWindow initialized")
        # print("[DASHBOARD] DashboardWindow initialized")

    def _setup_window(self):
        """Configure window"""
        self.setWindowTitle("DeskmateAI - Dashboard")
        self.setFixedSize(460, 580)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint |
            Qt.WindowType.WindowMinimizeButtonHint
        )
        self.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; }}")

    def _setup_ui(self):
        """Build UI matching Image 3"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(16, 16, 16, 16)
        main_layout.setSpacing(12)

        # ── Header ─────────────────────────────────────────
        header = QFrame()
        header.setFixedHeight(56)
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(14, 0, 14, 0)
        header_layout.setSpacing(10)

        # Mic icon
        mic = QLabel("🎙")
        mic.setStyleSheet("""
            QLabel {
                background: transparent;
                border: none;
                font-size: 20px;
            }
        """)
        header_layout.addWidget(mic)

        # Title
        title = QLabel("DeskmateAI")
        title.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 16px;
                font-weight: bold;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(title)
        header_layout.addStretch()

        # Username + active dot
        self._username_label = QLabel(self._username)
        self._username_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        header_layout.addWidget(self._username_label)

        self._active_dot = GlowDot(color=C['success'], size=8)
        header_layout.addWidget(self._active_dot)

        main_layout.addWidget(header)

        # ── Recent Commands Section ────────────────────────
        main_layout.addWidget(SectionTitle("RECENT COMMANDS"))

        # Commands container
        commands_frame = QFrame()
        commands_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        self._commands_layout = QVBoxLayout(commands_frame)
        self._commands_layout.setContentsMargins(0, 4, 0, 4)
        self._commands_layout.setSpacing(0)

        # Empty state
        self._empty_label = QLabel("No commands yet. Say 'Hey Deskmate' to start!")
        self._empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._empty_label.setFixedHeight(60)
        self._empty_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 12px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        self._commands_layout.addWidget(self._empty_label)

        main_layout.addWidget(commands_frame)

        # ── System Status Section ──────────────────────────
        main_layout.addWidget(SectionTitle("SYSTEM STATUS"))

        # Status grid
        status_grid = QGridLayout()
        status_grid.setSpacing(8)

        self._mic_card = StatusCard(
            icon="🎤", name="Microphone", state="inactive"
        )
        self._sbert_card = StatusCard(
            icon="🧠", name="SBERT", state="inactive"
        )
        self._ollama_card = StatusCard(
            icon="🤖", name="Ollama", state="inactive"
        )
        self._wake_card = StatusCard(
            icon="👂", name="Wake Word", state="inactive"
        )

        status_grid.addWidget(self._mic_card, 0, 0)
        status_grid.addWidget(self._sbert_card, 0, 1)
        status_grid.addWidget(self._ollama_card, 1, 0)
        status_grid.addWidget(self._wake_card, 1, 1)

        main_layout.addLayout(status_grid)
        main_layout.addStretch()

        # ── Footer Buttons ─────────────────────────────────
        footer_frame = QFrame()
        footer_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        footer_layout = QHBoxLayout(footer_frame)
        footer_layout.setContentsMargins(12, 8, 12, 8)
        footer_layout.setSpacing(8)

        settings_btn = FooterButton("⚙️", "Settings")
        settings_btn.clicked.connect(self.settings_requested.emit)
        footer_layout.addWidget(settings_btn)

        footer_layout.addStretch()

        logout_btn = FooterButton("→", "Logout")
        logout_btn.clicked.connect(self.logout_requested.emit)
        footer_layout.addWidget(logout_btn)

        exit_btn = FooterButton("✕", "Exit", danger=True)
        exit_btn.clicked.connect(self.exit_requested.emit)
        footer_layout.addWidget(exit_btn)

        main_layout.addWidget(footer_frame)

    # ── Data Updates ──────────────────────────────────────────

    def set_user(self, username, is_admin=False):
        """Update displayed username"""
        # print(f"[DASHBOARD] User: {username}")
        self._username = username
        self._is_admin = is_admin
        admin_tag = " ●" if is_admin else ""
        self._username_label.setText(f"{username}{admin_tag}")
        log_info(f"Dashboard user: {username}")

    def add_command(self, command, intent, success, time_str=None):
        """Add command to recent commands list"""
        # print(f"[DASHBOARD] Adding command: {command}")
        from datetime import datetime

        if time_str is None:
            time_str = datetime.now().strftime("%I:%M %p")

        # Remove empty state
        if self._empty_label.isVisible():
            self._empty_label.setVisible(False)

        # Add command row at top
        row = CommandRow(command, intent, success, time_str)
        self._commands_layout.insertWidget(0, row)

        # Keep only last 5
        while self._commands_layout.count() > 6:
            item = self._commands_layout.takeAt(
                self._commands_layout.count() - 1
            )
            if item.widget():
                item.widget().deleteLater()

        # Store in history
        self._command_history.insert(0, {
            "command": command,
            "intent": intent,
            "success": success,
            "time": time_str
        })
        if len(self._command_history) > 5:
            self._command_history = self._command_history[:5]

        log_debug(f"Command added: {command}")

    def update_from_history(self, history):
        """Update commands from context history"""
        # print(f"[DASHBOARD] Loading {len(history)} history items")
        if not history:
            return

        # Clear existing
        while self._commands_layout.count():
            item = self._commands_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self._empty_label.setVisible(False)

        for item in history[-5:]:
            from datetime import datetime
            time_str = item.get('timestamp', datetime.now().strftime("%I:%M %p"))
            if len(time_str) > 8:
                try:
                    dt = datetime.strptime(time_str, "%Y-%m-%d %H:%M:%S")
                    time_str = dt.strftime("%I:%M %p")
                except:
                    time_str = time_str[-8:]

            row = CommandRow(
                item.get('command', ''),
                item.get('intent', 'unknown'),
                True,
                time_str
            )
            self._commands_layout.addWidget(row)

        if self._commands_layout.count() == 0:
            self._empty_label.setVisible(True)
            self._commands_layout.addWidget(self._empty_label)

    def _refresh_status(self):
        """Refresh system status in background"""
        # print("[DASHBOARD] Refreshing status...")
        self._status_thread = SystemStatusThread(self)
        self._status_thread.status_ready.connect(self._update_status_cards)
        self._status_thread.start()

    def _update_status_cards(self, status):
        """Update status card states"""
        # print(f"[DASHBOARD] Status update: {status}")
        self._mic_card.set_state(status.get("microphone", "inactive"))
        self._sbert_card.set_state(status.get("sbert", "inactive"))
        self._ollama_card.set_state(status.get("ollama", "inactive"))
        self._wake_card.set_state(status.get("wake_word", "inactive"))

    def refresh(self):
        """Full dashboard refresh"""
        # print("[DASHBOARD] Full refresh...")
        log_info("Dashboard refresh")
        self._refresh_status()

        # Update command history from context
        try:
            from backend.core.context import get_context_manager
            context = get_context_manager()
            history = context.get_last_n_commands(5)
            if history:
                self.update_from_history(history)
        except Exception as e:
            # print(f"[DASHBOARD] History load error: {e}")
            log_error(f"Dashboard history error: {e}")

    def showEvent(self, event):
        """Refresh when window shown"""
        super().showEvent(event)
        self.refresh()

    def closeEvent(self, event):
        """Hide instead of close"""
        # print("[DASHBOARD] Hide on close")
        event.ignore()
        self.hide()