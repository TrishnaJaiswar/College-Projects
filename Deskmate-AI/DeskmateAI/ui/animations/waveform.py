# DeskmateAI/ui/animations/waveform.py

import os
import sys
import math
import random
from PyQt6.QtWidgets import QWidget
from PyQt6.QtCore import QTimer, QPropertyAnimation, pyqtProperty, Qt
from PyQt6.QtGui import QPainter, QColor, QPen, QBrush

# ============================================================
# WAVEFORM ANIMATION WIDGET FOR DESKMATEAI
# Animated cyan waveform bars shown when listening
# Matches the design from Image 2 (floating command window)
# and Image 1 (login screen)
# Bars animate smoothly up and down
# Level can be driven by real microphone input
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

# ── Color Constants ───────────────────────────────────────────

ACCENT_COLOR    = "#00D4FF"
ACCENT_DIM      = "#005566"
BACKGROUND      = "#0D1117"

# ── Waveform Widget ───────────────────────────────────────────

class WaveformWidget(QWidget):
    """
    Animated waveform bars widget
    Matches the cyan waveform from Image 2
    Can be driven by real mic levels or auto-animated
    """

    def __init__(self, parent=None,
                 num_bars=7,
                 bar_width=5,
                 bar_gap=4,
                 min_height=4,
                 max_height=40,
                 color=ACCENT_COLOR,
                 auto_animate=True):

        super().__init__(parent)

        self.num_bars = num_bars
        self.bar_width = bar_width
        self.bar_gap = bar_gap
        self.min_height = min_height
        self.max_height = max_height
        self.color = QColor(color)
        self.auto_animate = auto_animate

        # Current bar heights
        self.bar_heights = [min_height] * num_bars
        self.target_heights = [min_height] * num_bars

        # Animation phases for smooth natural movement
        self.phases = [random.uniform(0, 2 * math.pi) for _ in range(num_bars)]
        self.speeds = [random.uniform(0.05, 0.15) for _ in range(num_bars)]
        self.time = 0

        # State
        self._active = False
        self._audio_level = 0.0

        # Calculate widget size
        total_width = num_bars * bar_width + (num_bars - 1) * bar_gap
        self.setFixedSize(total_width + 20, max_height + 20)

        # Animation timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(50)  # 20 FPS - low CPU

        # print("[WAVEFORM] WaveformWidget initialized")

    def start(self):
        """Start waveform animation"""
        # print("[WAVEFORM] Starting animation")
        self._active = True
        self._timer.start()

    def stop(self):
        """Stop animation and reset bars"""
        # print("[WAVEFORM] Stopping animation")
        self._active = False
        self._timer.stop()
        self.bar_heights = [self.min_height] * self.num_bars
        self.update()

    def set_level(self, level):
        """
        Set audio level (0.0 to 1.0)
        Drives bar heights based on mic input
        """
        self._audio_level = max(0.0, min(1.0, level))

    def set_active(self, active):
        """Set active state"""
        if active:
            self.start()
        else:
            self.stop()

    def _animate(self):
        """Animate bar heights smoothly"""
        self.time += 1

        for i in range(self.num_bars):
            if self._audio_level > 0.01:
                # Drive by audio level with variation
                variation = math.sin(
                    self.time * self.speeds[i] + self.phases[i]
                ) * 0.3
                level = self._audio_level + variation
                level = max(0.0, min(1.0, level))
                target = self.min_height + level * (self.max_height - self.min_height)
            elif self.auto_animate:
                # Auto-animate with sine wave
                wave = math.sin(
                    self.time * self.speeds[i] + self.phases[i]
                )
                normalized = (wave + 1) / 2  # 0 to 1
                target = self.min_height + normalized * (
                    self.max_height - self.min_height
                ) * 0.7
            else:
                target = self.min_height

            # Smooth transition to target
            diff = target - self.bar_heights[i]
            self.bar_heights[i] += diff * 0.3

        self.update()

    def paintEvent(self, event):
        """Draw waveform bars"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Clear background
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        widget_height = self.height()
        total_width = self.num_bars * self.bar_width + (
            self.num_bars - 1
        ) * self.bar_gap
        start_x = (self.width() - total_width) // 2

        for i in range(self.num_bars):
            bar_h = max(self.min_height, int(self.bar_heights[i]))
            x = start_x + i * (self.bar_width + self.bar_gap)
            y = (widget_height - bar_h) // 2

            # Draw bar with rounded corners
            color = QColor(self.color)
            if not self._active:
                color.setAlpha(80)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(
                x, y,
                self.bar_width, bar_h,
                self.bar_width // 2,
                self.bar_width // 2
            )

        painter.end()


# ── Large Waveform (for floating window) ─────────────────────

class LargeWaveformWidget(WaveformWidget):
    """
    Larger waveform for the floating command window
    Matches Image 2 design exactly
    """

    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            num_bars=7,
            bar_width=8,
            bar_gap=6,
            min_height=8,
            max_height=60,
            color=ACCENT_COLOR,
            auto_animate=True
        )
        self.setFixedSize(120, 80)
        # print("[WAVEFORM] LargeWaveformWidget initialized")


# ── Small Waveform (for login screen) ────────────────────────

class SmallWaveformWidget(WaveformWidget):
    """
    Smaller waveform dots for login screen
    Matches the dot pattern in Image 1
    """

    def __init__(self, parent=None):
        super().__init__(
            parent=parent,
            num_bars=12,
            bar_width=6,
            bar_gap=4,
            min_height=6,
            max_height=20,
            color=ACCENT_COLOR,
            auto_animate=True
        )
        self.setFixedSize(200, 40)
        # print("[WAVEFORM] SmallWaveformWidget initialized")

    def paintEvent(self, event):
        """Draw as dots (like Image 1)"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        dot_size = self.bar_width
        total_width = self.num_bars * dot_size + (
            self.num_bars - 1
        ) * self.bar_gap
        start_x = (self.width() - total_width) // 2
        center_y = self.height() // 2

        for i in range(self.num_bars):
            # Dot size varies with bar height
            size_factor = self.bar_heights[i] / self.max_height
            size = max(4, int(dot_size * (0.5 + size_factor * 0.5)))
            x = start_x + i * (dot_size + self.bar_gap)
            y = center_y - size // 2

            color = QColor(ACCENT_COLOR)
            if not self._active:
                color.setAlpha(120)

            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(x, y, size, size)

        painter.end()


# ── Tray Icon Waveform (tiny, for system tray) ───────────────

class TrayWaveformWidget(QWidget):
    """
    Tiny waveform for system tray icon animation
    4 small bars that animate in tray icon
    """

    def __init__(self, parent=None):
        super().__init__(parent)

        self.num_bars = 4
        self.bar_width = 3
        self.bar_gap = 2
        self.min_height = 2
        self.max_height = 14

        self.bar_heights = [self.min_height] * self.num_bars
        self.phases = [random.uniform(0, 2 * math.pi) for _ in range(self.num_bars)]
        self.speeds = [random.uniform(0.08, 0.18) for _ in range(self.num_bars)]
        self.time = 0
        self._active = False

        total_width = self.num_bars * self.bar_width + (
            self.num_bars - 1
        ) * self.bar_gap
        self.setFixedSize(total_width + 4, self.max_height + 4)

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._animate)
        self._timer.setInterval(100)  # 10 FPS for tray
        # print("[WAVEFORM] TrayWaveformWidget initialized")

    def start(self):
        # print("[WAVEFORM] Tray waveform start")
        self._active = True
        self._timer.start()

    def stop(self):
        # print("[WAVEFORM] Tray waveform stop")
        self._active = False
        self._timer.stop()
        self.bar_heights = [self.min_height] * self.num_bars
        self.update()

    def _animate(self):
        self.time += 1
        for i in range(self.num_bars):
            wave = math.sin(self.time * self.speeds[i] + self.phases[i])
            normalized = (wave + 1) / 2
            target = self.min_height + normalized * (
                self.max_height - self.min_height
            )
            diff = target - self.bar_heights[i]
            self.bar_heights[i] += diff * 0.4
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(0, 0, 0, 0))

        widget_height = self.height()
        start_x = 2

        for i in range(self.num_bars):
            bar_h = max(self.min_height, int(self.bar_heights[i]))
            x = start_x + i * (self.bar_width + self.bar_gap)
            y = (widget_height - bar_h) // 2

            color = QColor(ACCENT_COLOR)
            painter.setBrush(QBrush(color))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(x, y, self.bar_width, bar_h, 1, 1)

        painter.end()

    def get_pixmap(self):
        """Get waveform as pixmap for tray icon"""
        from PyQt6.QtGui import QPixmap
        pixmap = QPixmap(self.size())
        pixmap.fill(QColor(0, 0, 0, 0))
        self.render(pixmap)
        return pixmap