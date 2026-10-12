# DeskmateAI/ui/tray_icon.py

import os
import sys
import math
import random
from PyQt6.QtWidgets import (
    QSystemTrayIcon, QMenu, QApplication, QWidget
)
from PyQt6.QtCore import QTimer, Qt, QThread, pyqtSignal, QPoint
from PyQt6.QtGui import (
    QIcon, QPixmap, QPainter, QColor, QBrush,
    QPen, QFont, QRadialGradient, QAction
)

# ============================================================
# SYSTEM TRAY ICON FOR DESKMATEAI
# Handles all tray icon states and animations
# States: idle, wakeword, listening, processing, muted
# Icon animates based on assistant state
# Right click shows context menu
# Left click shows/hides main window
# No window opens on command - icon just animates
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug

# ── Color Constants ───────────────────────────────────────────

COLORS = {
    "background":  QColor("#0D1117"),
    "surface":     QColor("#161B22"),
    "accent":      QColor("#00D4FF"),
    "success":     QColor("#3FB950"),
    "error":       QColor("#F85149"),
    "warning":     QColor("#D29922"),
    "inactive":    QColor("#484F58"),
    "muted":       QColor("#F85149"),
}

ICON_SIZE = 64  # Base icon size

# ── Icon States ───────────────────────────────────────────────

class IconState:
    IDLE       = "idle"
    WAKEWORD   = "wakeword"
    LISTENING  = "listening"
    PROCESSING = "processing"
    MUTED      = "muted"
    SUCCESS    = "success"
    ERROR      = "error"

# ── Icon Painter ──────────────────────────────────────────────

class TrayIconPainter:
    """
    Paints tray icon pixmaps for each state
    Matches the 5 icon states from first screenshot
    """

    def __init__(self, size=ICON_SIZE):
        self.size = size
        # print("[TRAY_PAINTER] Initialized")

    def _base_pixmap(self):
        """Create base transparent pixmap"""
        pixmap = QPixmap(self.size, self.size)
        pixmap.fill(QColor(0, 0, 0, 0))
        return pixmap

    def _draw_background(self, painter, color=None, radius=14):
        """Draw rounded square background"""
        bg_color = color or QColor("#161B22")
        painter.setBrush(QBrush(bg_color))
        painter.setPen(Qt.PenStyle.NoPen)
        margin = 4
        painter.drawRoundedRect(
            margin, margin,
            self.size - margin * 2,
            self.size - margin * 2,
            radius, radius
        )

    def _draw_microphone(self, painter, color, x_offset=0, scale=1.0):
        """Draw microphone icon"""
        cx = self.size // 2 + x_offset
        cy = self.size // 2 - 2

        # Scale
        mic_w = int(14 * scale)
        mic_h = int(18 * scale)
        mic_r = mic_w // 2

        # Microphone body
        mic_color = QColor(color)
        painter.setBrush(QBrush(mic_color))
        painter.setPen(Qt.PenStyle.NoPen)

        # Top capsule
        painter.drawRoundedRect(
            cx - mic_r, cy - mic_h // 2,
            mic_w, mic_h,
            mic_r, mic_r
        )

        # Stand arc
        pen = QPen(mic_color)
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        arc_r = int(10 * scale)
        painter.drawArc(
            cx - arc_r, cy + mic_h // 2 - arc_r,
            arc_r * 2, arc_r * 2,
            0, -180 * 16
        )

        # Stand line
        painter.drawLine(
            cx, cy + mic_h // 2,
            cx, cy + mic_h // 2 + int(5 * scale)
        )

        # Base line
        base_w = int(8 * scale)
        painter.drawLine(
            cx - base_w // 2, cy + mic_h // 2 + int(5 * scale),
            cx + base_w // 2, cy + mic_h // 2 + int(5 * scale)
        )

    def draw_idle(self):
        """STATE 1: Idle — static cyan mic, dark bg"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#161B22"))
        self._draw_microphone(painter, "#00D4FF")

        # Subtle border
        pen = QPen(QColor("#30363D"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        margin = 4
        painter.drawRoundedRect(
            margin, margin,
            self.size - margin * 2,
            self.size - margin * 2,
            14, 14
        )

        painter.end()
        return pixmap

    def draw_wakeword(self, pulse_size=0):
        """STATE 2: Wake word — glowing cyan pulse ring"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#0D1B22"))

        # Pulse ring
        if pulse_size > 0:
            cx = self.size // 2
            cy = self.size // 2
            pulse_color = QColor("#00D4FF")
            pulse_color.setAlpha(int(150 * (1 - pulse_size / 20)))
            pen = QPen(pulse_color)
            pen.setWidth(2)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            r = 18 + int(pulse_size)
            painter.drawEllipse(cx - r, cy - r, r * 2, r * 2)

        # Bright mic
        self._draw_microphone(painter, "#00D4FF", scale=1.1)

        # Cyan border glow
        pen = QPen(QColor("#00D4FF"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        margin = 3
        painter.drawRoundedRect(
            margin, margin,
            self.size - margin * 2,
            self.size - margin * 2,
            14, 14
        )

        painter.end()
        return pixmap

    def draw_listening(self, bar_heights=None):
        """STATE 3: Listening — mic left + waveform bars right"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#0D1B22"))

        # Mic on left side
        self._draw_microphone(painter, "#00D4FF", x_offset=-12, scale=0.75)

        # Waveform bars on right
        bar_heights = bar_heights or [8, 14, 10, 6]
        bar_width = 3
        bar_gap = 2
        start_x = self.size // 2 + 4
        center_y = self.size // 2

        painter.setPen(Qt.PenStyle.NoPen)
        for i, height in enumerate(bar_heights):
            x = start_x + i * (bar_width + bar_gap)
            y = center_y - height // 2
            painter.setBrush(QBrush(QColor("#00D4FF")))
            painter.drawRoundedRect(x, y, bar_width, height, 1, 1)

        # Cyan border
        pen = QPen(QColor("#00D4FF"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        margin = 3
        painter.drawRoundedRect(
            margin, margin,
            self.size - margin * 2,
            self.size - margin * 2,
            14, 14
        )

        painter.end()
        return pixmap

    def draw_processing(self, angle=0):
        """STATE 4: Processing — mic + rotating arc"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#161B22"))

        # Mic center
        self._draw_microphone(painter, "#00D4FF", scale=0.8)

        # Rotating arc
        pen = QPen(QColor("#00D4FF"))
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        margin = 6
        painter.drawArc(
            margin, margin,
            self.size - margin * 2,
            self.size - margin * 2,
            angle * 16,
            270 * 16
        )

        painter.end()
        return pixmap

    def draw_muted(self):
        """STATE 5: Muted — red diagonal line through mic"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#1A0D0D"))

        # Dimmed mic
        self._draw_microphone(painter, "#484F58")

        # Red diagonal line
        pen = QPen(QColor("#F85149"))
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        margin = 12
        painter.drawLine(
            margin, margin,
            self.size - margin,
            self.size - margin
        )

        # Red border
        pen = QPen(QColor("#F85149"))
        pen.setWidth(1)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        m = 4
        painter.drawRoundedRect(m, m, self.size - m*2, self.size - m*2, 14, 14)

        painter.end()
        return pixmap

    def draw_success_flash(self):
        """Brief green flash for success"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#0D1A0D"))
        self._draw_microphone(painter, "#3FB950")

        pen = QPen(QColor("#3FB950"))
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)
        m = 3
        painter.drawRoundedRect(m, m, self.size - m*2, self.size - m*2, 14, 14)

        painter.end()
        return pixmap

    def draw_error_flash(self):
        """Brief red flash for error"""
        pixmap = self._base_pixmap()
        painter = QPainter(pixmap)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        self._draw_background(painter, QColor("#1A0D0D"))
        self._draw_microphone(painter, "#F85149")

        painter.end()
        return pixmap


# ── Tray Icon Manager ─────────────────────────────────────────

class TrayIconManager(QSystemTrayIcon):
    """
    Main system tray icon manager
    Handles all states and animations
    Provides right-click menu
    """

    # Signals
    show_dashboard = pyqtSignal()
    show_settings = pyqtSignal()
    add_new_user = pyqtSignal()
    switch_user = pyqtSignal()
    logout_requested = pyqtSignal()
    exit_requested = pyqtSignal()
    mute_toggled = pyqtSignal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        from PyQt6.QtWidgets import QApplication
        from PyQt6.QtGui import QIcon
        # 🔥 FORCE VALID ICON BEFORE ANYTHING
        self.setIcon(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        ))
        from PyQt6.QtWidgets import QSystemTrayIcon

        if not QSystemTrayIcon.isSystemTrayAvailable():
            print("❌ System tray NOT available — skipping tray")
            return

        self._painter = TrayIconPainter(ICON_SIZE)
        # 🔥 FORCE SAFE ICON IMMEDIATELY
        self.setIcon(QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_ComputerIcon
        ))
        self._state = IconState.IDLE
        self._muted = False
        self._current_user = "User"
        self._is_admin = False

        # Animation variables
        self._pulse_size = 0
        self._pulse_growing = True
        self._angle = 0
        self._bar_heights = [8, 14, 10, 6]
        self._bar_phases = [random.uniform(0, 6.28) for _ in range(4)]
        self._bar_time = 0
        self._flash_count = 0

        # Animation timer
        self._anim_timer = QTimer(self)
        self._anim_timer.timeout.connect(self._update_animation)
        self._anim_timer.setInterval(80)  # ~12 FPS for tray

        # Flash timer (for success/error)
        self._flash_timer = QTimer(self)
        self._flash_timer.timeout.connect(self._end_flash)
        self._flash_timer.setSingleShot(True)

        # Setup
        self._setup_menu()
        self._set_icon_state(IconState.IDLE)

        # Connect click
        self.activated.connect(self._on_activated)

        # Start animation
        self._anim_timer.start()

        log_info("TrayIconManager initialized")
        # print("[TRAY] TrayIconManager initialized")

    # ── Menu Setup ────────────────────────────────────────────

    def _setup_menu(self):
        """Setup right-click context menu"""
        # print("[TRAY] Setting up context menu")
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #161B22;
                border: 1px solid #30363D;
                border-radius: 8px;
                padding: 4px;
                color: #E6EDF3;
                font-family: 'Segoe UI';
                font-size: 13px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 4px;
            }
            QMenu::item:selected {
                background-color: #1C2128;
                color: #00D4FF;
            }
            QMenu::separator {
                height: 1px;
                background: #30363D;
                margin: 4px 8px;
            }
        """)

        # Header (non-clickable)
        self._header_action = QAction("🎙 DeskmateAI", self)
        self._header_action.setEnabled(False)
        menu.addAction(self._header_action)

        self._user_action = QAction("👤 User", self)
        self._user_action.setEnabled(False)
        menu.addAction(self._user_action)

        menu.addSeparator()

        # Dashboard
        dashboard_action = QAction("📊 Open Dashboard", self)
        dashboard_action.triggered.connect(self.show_dashboard.emit)
        menu.addAction(dashboard_action)

        # Settings
        settings_action = QAction("⚙️ Settings", self)
        settings_action.triggered.connect(self.show_settings.emit)
        menu.addAction(settings_action)

        menu.addSeparator()

        # Mute
        self._mute_action = QAction("🔇 Mute Assistant", self)
        self._mute_action.triggered.connect(self._toggle_mute)
        menu.addAction(self._mute_action)

        # Switch User
        switch_action = QAction("👥 Switch User", self)
        switch_action.triggered.connect(self.switch_user.emit)
        menu.addAction(switch_action)

        # Add New User
        self._add_user_action = QAction("➕ Add New User", self)
        self._add_user_action.triggered.connect(self.add_new_user.emit)
        menu.addAction(self._add_user_action)

        menu.addSeparator()

        # Logout
        logout_action = QAction("🔒 Logout", self)
        logout_action.triggered.connect(self.logout_requested.emit)
        menu.addAction(logout_action)

        # Exit
        exit_action = QAction("❌ Exit", self)
        exit_action.triggered.connect(self.exit_requested.emit)
        menu.addAction(exit_action)

        self.setContextMenu(menu)
        # print("[TRAY] ✅ Context menu setup complete")

    # ── User Info ─────────────────────────────────────────────

    def set_user(self, username, is_admin=False):
        """Update displayed username"""
        # print(f"[TRAY] User: {username} | Admin: {is_admin}")
        self._current_user = username
        self._is_admin = is_admin
        admin_tag = " (Admin)" if is_admin else ""
        self._user_action.setText(f"👤 {username}{admin_tag}")

        # Show add user only for admins
        self._add_user_action.setVisible(is_admin)

    # ── State Management ──────────────────────────────────────

    def set_state(self, state):
        """Set tray icon state"""
        # print(f"[TRAY] State: {state}")
        log_debug(f"Tray state: {state}")

        if self._muted and state != IconState.MUTED:
            return

        self._state = state
        self._set_icon_state(state)

        # Handle flash states
        if state == IconState.SUCCESS:
            self._flash_timer.start(600)
        elif state == IconState.ERROR:
            self._flash_timer.start(600)

    def _set_icon_state(self, state):
        """Set icon pixmap for state"""
        if state == IconState.IDLE:
            pixmap = self._painter.draw_idle()
        elif state == IconState.WAKEWORD:
            pixmap = self._painter.draw_wakeword(0)
        elif state == IconState.LISTENING:
            pixmap = self._painter.draw_listening()
        elif state == IconState.PROCESSING:
            pixmap = self._painter.draw_processing(0)
        elif state == IconState.MUTED:
            pixmap = self._painter.draw_muted()
        elif state == IconState.SUCCESS:
            pixmap = self._painter.draw_success_flash()
        elif state == IconState.ERROR:
            pixmap = self._painter.draw_error_flash()
        else:
            pixmap = self._painter.draw_idle()

        self.setIcon(QIcon(pixmap))

    # ── Animation ─────────────────────────────────────────────

    def _update_animation(self):
        """Update animated icon frame"""
        if self._muted:
            return

        if self._state == IconState.WAKEWORD:
            # Pulse animation
            if self._pulse_growing:
                self._pulse_size += 1.5
                if self._pulse_size >= 20:
                    self._pulse_growing = False
            else:
                self._pulse_size -= 1.5
                if self._pulse_size <= 0:
                    self._pulse_growing = True
                    self._pulse_size = 0

            pixmap = self._painter.draw_wakeword(self._pulse_size)
            self.setIcon(QIcon(pixmap))

        elif self._state == IconState.LISTENING:
            # Waveform animation
            self._bar_time += 1
            for i in range(4):
                wave = math.sin(
                    self._bar_time * 0.12 + self._bar_phases[i]
                )
                normalized = (wave + 1) / 2
                self._bar_heights[i] = int(4 + normalized * 12)

            pixmap = self._painter.draw_listening(self._bar_heights)
            self.setIcon(QIcon(pixmap))

        elif self._state == IconState.PROCESSING:
            # Rotation animation
            self._angle = (self._angle + 15) % 360
            pixmap = self._painter.draw_processing(self._angle)
            self.setIcon(QIcon(pixmap))

    def _end_flash(self):
        """End flash and return to idle"""
        # print("[TRAY] Flash ended, returning to idle")
        self._state = IconState.IDLE
        self._set_icon_state(IconState.IDLE)

    # ── Mute ──────────────────────────────────────────────────

    def _toggle_mute(self):
        """Toggle mute state"""
        self._muted = not self._muted
        # print(f"[TRAY] Mute: {self._muted}")
        log_info(f"Tray mute toggled: {self._muted}")

        if self._muted:
            self._mute_action.setText("🔊 Unmute Assistant")
            self._set_icon_state(IconState.MUTED)
        else:
            self._mute_action.setText("🔇 Mute Assistant")
            self._set_icon_state(IconState.IDLE)

        self.mute_toggled.emit(self._muted)

    def is_muted(self):
        return self._muted

    # ── Click Handler ─────────────────────────────────────────

    def _on_activated(self, reason):
        """Handle tray icon click"""
        # print(f"[TRAY] Activated: {reason}")
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            # Left click — toggle dashboard
            # print("[TRAY] Left click — showing dashboard")
            self.show_dashboard.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            # Double click — show dashboard
            self.show_dashboard.emit()
        print("Tray clicked or active")

    # ── Tooltip ───────────────────────────────────────────────

    def update_tooltip(self, status_text):
        """Update tray tooltip"""
        self.setToolTip(f"DeskmateAI — {status_text}")

    # ── Notification ──────────────────────────────────────────

    def show_notification(self, title, message,
                          duration=3000,
                          icon=QSystemTrayIcon.MessageIcon.Information):
        """Show system notification"""
        # print(f"[TRAY] Notification: {title} — {message}")
        log_info(f"Notification: {title}")
        self.showMessage(title, message, icon, duration)

    # ── Cleanup ───────────────────────────────────────────────

    def cleanup(self):
        """Clean up timers"""
        # print("[TRAY] Cleaning up...")
        self._anim_timer.stop()
        self._flash_timer.stop()
        self.hide()
        log_info("TrayIconManager cleaned up")
    
print("✅ Tray fully initialized and visible")