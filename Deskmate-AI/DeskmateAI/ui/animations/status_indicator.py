# DeskmateAI/ui/animations/status_indicator.py

import os
import sys
import math
from PyQt6.QtWidgets import QWidget, QLabel, QHBoxLayout
from PyQt6.QtCore import QTimer, Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt6.QtGui import QPainter, QColor, QBrush, QPen, QFont

# ============================================================
# STATUS INDICATOR WIDGETS FOR DESKMATEAI
# Animated status dots and indicators
# Used in:
# - Dashboard system status cards (Image 3)
# - Tray icon states
# - Floating window status text
# - Login screen state
# ============================================================

# ── Color Constants ───────────────────────────────────────────

COLORS = {
    "background":  "#0D1117",
    "surface":     "#161B22",
    "surface2":    "#1C2128",
    "border":      "#30363D",
    "accent":      "#00D4FF",
    "text":        "#E6EDF3",
    "subtext":     "#8B949E",
    "success":     "#3FB950",
    "error":       "#F85149",
    "warning":     "#D29922",
    "inactive":    "#484F58",
}

# ── Status Dot Widget ─────────────────────────────────────────

class StatusDot(QWidget):
    """
    Animated status dot
    Matches the colored dots in Image 3 dashboard
    Pulses when active
    """

    STATES = {
        "active":    "#00D4FF",   # cyan - listening/active
        "success":   "#3FB950",   # green - ready/working
        "error":     "#F85149",   # red - error
        "warning":   "#D29922",   # yellow - warning
        "inactive":  "#484F58",   # grey - offline
        "processing": "#D29922",  # yellow - processing
    }

    def __init__(self, parent=None, size=10, state="inactive"):
        super().__init__(parent)

        self._size = size
        self._state = state
        self._opacity = 1.0
        self._pulse_growing = False
        self._pulse_size = 0

        self.setFixedSize(size + 10, size + 10)

        # Pulse timer
        self._pulse_timer = QTimer(self)
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.setInterval(50)

        # print(f"[STATUS_DOT] Initialized: state={state}")

    def set_state(self, state):
        """Set dot state"""
        # print(f"[STATUS_DOT] State: {state}")
        self._state = state

        # Start pulsing for active states
        if state in ["active", "processing"]:
            self._pulse_timer.start()
        else:
            self._pulse_timer.stop()
            self._pulse_size = 0

        self.update()

    def get_state(self):
        return self._state

    def _update_pulse(self):
        """Update pulse animation"""
        if self._pulse_growing:
            self._pulse_size += 0.8
            if self._pulse_size >= self._size * 0.8:
                self._pulse_growing = False
        else:
            self._pulse_size -= 0.8
            if self._pulse_size <= 0:
                self._pulse_growing = True
                self._pulse_size = 0

        self.update()

    def paintEvent(self, event):
        """Draw status dot"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        center_x = self.width() // 2
        center_y = self.height() // 2
        color = QColor(self.STATES.get(self._state, self.STATES["inactive"]))

        # Draw pulse ring for active states
        if self._state in ["active", "processing"] and self._pulse_size > 0:
            pulse_color = QColor(color)
            pulse_color.setAlpha(int(100 * (1 - self._pulse_size / (self._size * 0.8))))
            painter.setBrush(QBrush(pulse_color))
            painter.setPen(Qt.PenStyle.NoPen)
            pulse_r = int(self._size // 2 + self._pulse_size)
            painter.drawEllipse(
                center_x - pulse_r,
                center_y - pulse_r,
                pulse_r * 2,
                pulse_r * 2
            )

        # Draw main dot
        painter.setBrush(QBrush(color))
        painter.setPen(Qt.PenStyle.NoPen)
        r = self._size // 2
        painter.drawEllipse(
            center_x - r,
            center_y - r,
            r * 2, r * 2
        )

        painter.end()


# ── Status Card Widget ────────────────────────────────────────

class StatusCard(QWidget):
    """
    Status card with icon, name and dot
    Matches the system status cards in Image 3
    e.g. "🎤 Microphone ●"
    """

    def __init__(self, parent=None, icon="🎤",
                 name="Microphone", state="inactive"):
        super().__init__(parent)

        self._state = state
        self.setFixedHeight(50)
        self.setMinimumWidth(160)

        # Styling
        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 8px;
            }}
        """)

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 8, 12, 8)
        layout.setSpacing(8)

        # Icon
        self._icon_label = QLabel(icon)
        self._icon_label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {COLORS['subtext']};
                font-size: 16px;
            }}
        """)
        self._icon_label.setFixedWidth(24)
        layout.addWidget(self._icon_label)

        # Name
        self._name_label = QLabel(name)
        self._name_label.setStyleSheet(f"""
            QLabel {{
                background: transparent;
                border: none;
                color: {COLORS['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
            }}
        """)
        layout.addWidget(self._name_label)
        layout.addStretch()

        # Status dot
        self._dot = StatusDot(size=10, state=state)
        layout.addWidget(self._dot)

        # print(f"[STATUS_CARD] Initialized: {name}")

    def set_state(self, state):
        """Update card state"""
        # print(f"[STATUS_CARD] {self._name_label.text()} → {state}")
        self._state = state
        self._dot.set_state(state)

        # Update border color based on state
        border_color = {
            "success": COLORS["success"],
            "active":  COLORS["accent"],
            "error":   COLORS["error"],
            "warning": COLORS["warning"],
            "inactive": COLORS["border"],
            "processing": COLORS["warning"]
        }.get(state, COLORS["border"])

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {COLORS['surface']};
                border: 1px solid {border_color};
                border-radius: 8px;
            }}
        """)


# ── Status Text Label ─────────────────────────────────────────

class StatusLabel(QWidget):
    """
    Animated status text label
    Shows: Listening... / Processing... / Done / Error
    Matches the status text in Image 2 floating window
    """

    STATUS_COLORS = {
        "idle":        "#8B949E",
        "listening":   "#00D4FF",
        "processing":  "#D29922",
        "executing":   "#D29922",
        "success":     "#3FB950",
        "error":       "#F85149",
        "wakeword":    "#00D4FF",
    }

    STATUS_TEXTS = {
        "idle":        "Idle",
        "listening":   "LISTENING...",
        "processing":  "PROCESSING...",
        "executing":   "EXECUTING...",
        "success":     "DONE",
        "error":       "ERROR",
        "wakeword":    "WAKE WORD DETECTED",
    }

    def __init__(self, parent=None, initial_status="idle"):
        super().__init__(parent)

        self._status = initial_status
        self._dot_count = 0
        self._opacity = 255

        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # Status label
        self._label = QLabel(
            self.STATUS_TEXTS.get(initial_status, "Idle")
        )
        self._label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._label.setStyleSheet(f"""
            QLabel {{
                color: {self.STATUS_COLORS.get(initial_status, COLORS['subtext'])};
                font-size: 13px;
                font-weight: bold;
                font-family: 'Segoe UI';
                letter-spacing: 2px;
                background: transparent;
                border: none;
            }}
        """)
        layout.addWidget(self._label)

        # Dot animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._update_dots)
        self._timer.setInterval(500)

        # print(f"[STATUS_LABEL] Initialized: {initial_status}")

    def set_status(self, status):
        """Update status"""
        # print(f"[STATUS_LABEL] Status: {status}")
        self._status = status
        self._dot_count = 0

        color = self.STATUS_COLORS.get(status, COLORS["subtext"])
        text = self.STATUS_TEXTS.get(status, status.upper())

        self._label.setText(text)
        self._label.setStyleSheet(f"""
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

        # Animate dots for active states
        if status in ["listening", "processing", "executing"]:
            self._timer.start()
        else:
            self._timer.stop()

    def _update_dots(self):
        """Animate trailing dots"""
        self._dot_count = (self._dot_count + 1) % 4
        base_text = self.STATUS_TEXTS.get(
            self._status, self._status.upper()
        ).rstrip('.')
        dots = '.' * self._dot_count
        self._label.setText(f"{base_text}{dots}")


# ── Glow Dot (for user active indicator) ─────────────────────

class GlowDot(QWidget):
    """
    Simple glowing green dot
    Used next to username in dashboard (Image 3)
    Shows user is active/online
    """

    def __init__(self, parent=None, color="#3FB950", size=8):
        super().__init__(parent)
        self._color = QColor(color)
        self._size = size
        self._glow = 0
        self._growing = True
        self.setFixedSize(size + 8, size + 8)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._pulse)
        self._timer.setInterval(60)
        self._timer.start()
        # print("[GLOW_DOT] Initialized")

    def _pulse(self):
        if self._growing:
            self._glow += 1
            if self._glow >= 8:
                self._growing = False
        else:
            self._glow -= 1
            if self._glow <= 0:
                self._growing = True
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        cx = self.width() // 2
        cy = self.height() // 2

        # Glow
        if self._glow > 0:
            glow_color = QColor(self._color)
            glow_color.setAlpha(int(60 * self._glow / 8))
            painter.setBrush(QBrush(glow_color))
            painter.setPen(Qt.PenStyle.NoPen)
            gr = self._size // 2 + self._glow
            painter.drawEllipse(cx - gr, cy - gr, gr * 2, gr * 2)

        # Main dot
        painter.setBrush(QBrush(self._color))
        painter.setPen(Qt.PenStyle.NoPen)
        r = self._size // 2
        painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        painter.end()


# ── Processing Spinner ────────────────────────────────────────

class ProcessingSpinner(QWidget):
    """
    Rotating arc spinner
    Used for processing state in tray icon
    """

    def __init__(self, parent=None, size=30, color="#00D4FF"):
        super().__init__(parent)
        self._size = size
        self._color = QColor(color)
        self._angle = 0
        self.setFixedSize(size, size)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._rotate)
        self._timer.setInterval(30)
        # print("[SPINNER] Initialized")

    def start(self):
        # print("[SPINNER] Starting")
        self._timer.start()

    def stop(self):
        # print("[SPINNER] Stopping")
        self._timer.stop()
        self.update()

    def _rotate(self):
        self._angle = (self._angle + 12) % 360
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        pen = QPen(self._color)
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        margin = 4
        rect_size = self._size - margin * 2
        painter.drawArc(
            margin, margin,
            rect_size, rect_size,
            self._angle * 16,
            270 * 16  # 270 degree arc
        )

        painter.end()