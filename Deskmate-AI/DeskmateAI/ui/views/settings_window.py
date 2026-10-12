# DeskmateAI/ui/views/settings_window.py

import os
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QLineEdit, QSlider,
    QScrollArea, QStackedWidget, QRadioButton,
    QButtonGroup, QListWidget, QListWidgetItem,
    QDialog, QTextEdit, QSizePolicy, QGridLayout
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QIcon

# ============================================================
# SETTINGS WINDOW FOR DESKMATEAI
# Matches Image 4 design exactly
# Two panel layout:
# Left sidebar: navigation items
# Right content: settings panels
# Panels:
# - Profile
# - Language
# - Wake Word
# - Intents
# - Security
# - Users
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, BASE_DIR)

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
    "sidebar":  "#0D1117",
}

# ── Sidebar Nav Item ──────────────────────────────────────────

class NavItem(QPushButton):
    """
    Sidebar navigation item
    Matches Image 4 sidebar items
    Highlights cyan when active
    """

    def __init__(self, icon, text, parent=None):
        super().__init__(parent)
        self.setText(f"  {icon}   {text}")
        self.setFixedHeight(44)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._update_style(False)

    def _update_style(self, active):
        if active:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['surface2']};
                    border: none;
                    border-left: 3px solid {C['accent']};
                    border-radius: 0px;
                    color: {C['accent']};
                    font-size: 13px;
                    font-family: 'Segoe UI';
                    text-align: left;
                    padding-left: 14px;
                }}
            """)
        else:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-left: 3px solid transparent;
                    border-radius: 0px;
                    color: {C['subtext']};
                    font-size: 13px;
                    font-family: 'Segoe UI';
                    text-align: left;
                    padding-left: 14px;
                }}
                QPushButton:hover {{
                    background-color: {C['surface2']};
                    color: {C['text']};
                }}
            """)

    def setChecked(self, checked):
        super().setChecked(checked)
        self._update_style(checked)


# ── Settings Button ───────────────────────────────────────────

class SettingsButton(QPushButton):
    """Standard settings action button"""

    def __init__(self, text, primary=False, danger=False, parent=None):
        super().__init__(text, parent)
        self.setFixedHeight(44)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        if primary:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: {C['accent']};
                    border: none;
                    border-radius: 8px;
                    color: #0D1117;
                    font-size: 14px;
                    font-weight: bold;
                    font-family: 'Segoe UI';
                }}
                QPushButton:hover {{ background-color: #00AACC; }}
                QPushButton:pressed {{ background-color: #007799; }}
            """)
        elif danger:
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    border: 1px solid {C['error']};
                    border-radius: 8px;
                    color: {C['error']};
                    font-size: 13px;
                    font-family: 'Segoe UI';
                }}
                QPushButton:hover {{ background-color: #1A0D0D; }}
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
                }}
                QPushButton:hover {{
                    border-color: {C['accent']};
                    color: {C['accent']};
                }}
            """)


# ── Panel Title ───────────────────────────────────────────────

class PanelTitle(QLabel):
    """Panel content title"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 20px;
                font-weight: bold;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        self.setFixedHeight(40)


# ── Radio Button ──────────────────────────────────────────────

class StyledRadio(QRadioButton):
    """Styled radio button matching Image 4"""

    def __init__(self, text, parent=None):
        super().__init__(text, parent)
        self.setStyleSheet(f"""
            QRadioButton {{
                color: {C['text']};
                font-size: 14px;
                font-family: 'Segoe UI';
                background: transparent;
                spacing: 10px;
                padding: 6px 0;
            }}
            QRadioButton::indicator {{
                width: 18px;
                height: 18px;
                border-radius: 9px;
                border: 2px solid {C['border']};
                background: transparent;
            }}
            QRadioButton::indicator:checked {{
                border: 2px solid {C['accent']};
                background: {C['accent']};
            }}
            QRadioButton::indicator:hover {{
                border: 2px solid {C['accent']};
            }}
        """)


# ── Profile Panel ─────────────────────────────────────────────

class ProfilePanel(QWidget):
    """Profile settings panel"""

    profile_updated = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(PanelTitle("Profile"))

        # Avatar
        avatar_layout = QHBoxLayout()
        self._avatar = QLabel("U")
        self._avatar.setFixedSize(64, 64)
        self._avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {C['surface2']};
                border: 2px solid {C['accent']};
                border-radius: 32px;
                color: {C['accent']};
                font-size: 28px;
                font-weight: bold;
                font-family: 'Segoe UI';
            }}
        """)
        avatar_layout.addWidget(self._avatar)
        avatar_layout.addSpacing(16)

        info_layout = QVBoxLayout()
        self._name_label = QLabel("Username")
        self._name_label.setStyleSheet(f"""
            QLabel {{
                color: {C['text']};
                font-size: 18px;
                font-weight: bold;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        info_layout.addWidget(self._name_label)

        self._role_label = QLabel("User")
        self._role_label.setStyleSheet(f"""
            QLabel {{
                color: {C['subtext']};
                font-size: 13px;
                font-family: 'Segoe UI';
                background: transparent;
                border: none;
            }}
        """)
        info_layout.addWidget(self._role_label)
        avatar_layout.addLayout(info_layout)
        avatar_layout.addStretch()
        layout.addLayout(avatar_layout)

        # Divider
        divider = QFrame()
        divider.setFrameShape(QFrame.Shape.HLine)
        divider.setStyleSheet(f"color: {C['border']};")
        layout.addWidget(divider)

        # Change Password
        layout.addWidget(QLabel("Change Password", styleSheet=f"""
            color: {C['text']}; font-size: 13px;
            font-family: 'Segoe UI'; background: transparent; border: none;
        """))

        self._old_pass = QLineEdit()
        self._old_pass.setPlaceholderText("Current password")
        self._old_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._old_pass.setFixedHeight(40)
        self._old_pass.setStyleSheet(self._input_style())
        layout.addWidget(self._old_pass)

        self._new_pass = QLineEdit()
        self._new_pass.setPlaceholderText("New password")
        self._new_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._new_pass.setFixedHeight(40)
        self._new_pass.setStyleSheet(self._input_style())
        layout.addWidget(self._new_pass)

        self._confirm_pass = QLineEdit()
        self._confirm_pass.setPlaceholderText("Confirm new password")
        self._confirm_pass.setEchoMode(QLineEdit.EchoMode.Password)
        self._confirm_pass.setFixedHeight(40)
        self._confirm_pass.setStyleSheet(self._input_style())
        layout.addWidget(self._confirm_pass)

        self._pass_status = QLabel("")
        self._pass_status.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 12px;
            background: transparent; border: none; }}
        """)
        layout.addWidget(self._pass_status)

        change_btn = SettingsButton("Change Password", primary=True)
        change_btn.clicked.connect(self._change_password)
        layout.addWidget(change_btn)

        layout.addStretch()

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 12px;
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """

    def set_user(self, username, is_admin):
        self._username = username
        self._avatar.setText(username[0].upper() if username else "U")
        self._name_label.setText(username)
        self._role_label.setText("Admin" if is_admin else "User")

    def _change_password(self):
        old = self._old_pass.text()
        new = self._new_pass.text()
        confirm = self._confirm_pass.text()

        if not old or not new:
            self._pass_status.setText("Please fill all fields")
            self._pass_status.setStyleSheet(f"""
                QLabel {{ color: {C['error']}; font-size: 12px;
                background: transparent; border: none; }}
            """)
            return

        if new != confirm:
            self._pass_status.setText("Passwords do not match")
            self._pass_status.setStyleSheet(f"""
                QLabel {{ color: {C['error']}; font-size: 12px;
                background: transparent; border: none; }}
            """)
            return

        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()
            success, message = auth.change_password(self._username, old, new)

            if success:
                self._pass_status.setText("✅ Password changed")
                self._pass_status.setStyleSheet(f"""
                    QLabel {{ color: {C['success']}; font-size: 12px;
                    background: transparent; border: none; }}
                """)
                self._old_pass.clear()
                self._new_pass.clear()
                self._confirm_pass.clear()
            else:
                self._pass_status.setText(f"❌ {message}")
                self._pass_status.setStyleSheet(f"""
                    QLabel {{ color: {C['error']}; font-size: 12px;
                    background: transparent; border: none; }}
                """)
        except Exception as e:
            log_error(f"Change password error: {e}")


# ── Language Panel ────────────────────────────────────────────

class LanguagePanel(QWidget):
    """
    Language + Wake Word settings
    Matches Image 4 exactly
    """

    language_changed = pyqtSignal(str, str)
    wake_word_changed = pyqtSignal(str, float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(14)

        layout.addWidget(PanelTitle("Language Settings"))

        # Language radio buttons
        self._lang_group = QButtonGroup(self)
        self._en_radio = StyledRadio("English")
        self._hi_radio = StyledRadio("Hindi")
        self._mr_radio = StyledRadio("Marathi")
        self._hinglish_radio = StyledRadio("Hinglish (Hindi+English)")
        self._minglish_radio = StyledRadio("Minglish (Marathi+English)")

        self._lang_group.addButton(self._en_radio, 0)
        self._lang_group.addButton(self._hi_radio, 1)
        self._lang_group.addButton(self._mr_radio, 2)
        self._lang_group.addButton(self._hinglish_radio, 3)
        self._lang_group.addButton(self._minglish_radio, 4)
        self._en_radio.setChecked(True)

        layout.addWidget(self._en_radio)
        layout.addWidget(self._hi_radio)
        layout.addWidget(self._mr_radio)
        layout.addWidget(self._hinglish_radio)
        layout.addWidget(self._minglish_radio)

        layout.addSpacing(8)

        # Wake Word
        wake_label = QLabel("Wake Word")
        wake_label.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 13px;
            font-family: 'Segoe UI'; background: transparent; border: none; }}
        """)
        layout.addWidget(wake_label)

        self._wake_input = QLineEdit()
        self._wake_input.setPlaceholderText("e.g., Hey Deskmate")
        self._wake_input.setFixedHeight(46)
        self._wake_input.setStyleSheet(f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 10px;
                color: {C['text']};
                font-size: 14px;
                font-family: 'Segoe UI';
                padding: 0 14px;
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """)
        layout.addWidget(self._wake_input)

        # Sensitivity slider
        sens_layout = QHBoxLayout()
        sens_label = QLabel("Sensitivity")
        sens_label.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 13px;
            font-family: 'Segoe UI'; background: transparent; border: none; }}
        """)
        sens_layout.addWidget(sens_label)
        sens_layout.addStretch()

        self._sens_value = QLabel("60%")
        self._sens_value.setStyleSheet(f"""
            QLabel {{ color: {C['accent']}; font-size: 13px;
            font-weight: bold; background: transparent; border: none; }}
        """)
        sens_layout.addWidget(self._sens_value)
        layout.addLayout(sens_layout)

        self._sens_slider = QSlider(Qt.Orientation.Horizontal)
        self._sens_slider.setMinimum(10)
        self._sens_slider.setMaximum(100)
        self._sens_slider.setValue(60)
        self._sens_slider.valueChanged.connect(
            lambda v: self._sens_value.setText(f"{v}%")
        )
        self._sens_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                height: 6px;
                background: {C['border']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background: {C['accent']};
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::sub-page:horizontal {{
                background: {C['accent']};
                border-radius: 3px;
            }}
        """)
        layout.addWidget(self._sens_slider)

        # Test wake word button
        test_btn = SettingsButton("Test Wake Word")
        test_btn.clicked.connect(self._test_wake_word)
        layout.addWidget(test_btn)

        self._test_status = QLabel("")
        self._test_status.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 12px;
            background: transparent; border: none; }}
        """)
        layout.addWidget(self._test_status)

        # Save button
        save_btn = SettingsButton("Save Changes", primary=True)
        save_btn.clicked.connect(self._save_changes)
        layout.addWidget(save_btn)

        layout.addStretch()

    def set_user(self, username, profile):
        self._username = username
        lang = profile.get('language', 'en')
        if lang == 'hi':
            self._hi_radio.setChecked(True)
        elif lang == 'mr':
            self._mr_radio.setChecked(True)
        elif lang == 'hinglish':
            self._hinglish_radio.setChecked(True)
        elif lang == 'minglish':
            self._minglish_radio.setChecked(True)
        else:
            self._en_radio.setChecked(True)

        self._wake_input.setText(profile.get('wake_word', 'hey deskmate'))
        sensitivity = int(profile.get('wake_word_sensitivity', 0.6) * 100)
        self._sens_slider.setValue(sensitivity)

    def _get_selected_language(self):
        if self._hi_radio.isChecked():
            return 'hi', 'Hindi'
        elif self._mr_radio.isChecked():
            return 'mr', 'Marathi'
        elif self._hinglish_radio.isChecked():
            return 'hinglish', 'Hinglish'
        elif self._minglish_radio.isChecked():
            return 'minglish', 'Minglish'
        return 'en', 'English'

    def _test_wake_word(self):
        wake_word = self._wake_input.text().strip()
        if not wake_word:
            return
        self._test_status.setText("🎤 Say your wake word now...")
        QTimer.singleShot(
            8000,
            lambda: self._test_status.setText("")
        )

    def _save_changes(self):
        try:
            lang_code, lang_name = self._get_selected_language()
            wake_word = self._wake_input.text().strip() or "hey deskmate"
            sensitivity = self._sens_slider.value() / 100.0

            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()

            auth.update_language(self._username, lang_code, lang_name)
            auth.update_wake_word(self._username, wake_word, sensitivity)

            self.language_changed.emit(lang_code, lang_name)
            self.wake_word_changed.emit(wake_word, sensitivity)

            self._test_status.setText("✅ Settings saved")
            self._test_status.setStyleSheet(f"""
                QLabel {{ color: {C['success']}; font-size: 12px;
                background: transparent; border: none; }}
            """)
            QTimer.singleShot(
                3000,
                lambda: self._test_status.setText("")
            )
        except Exception as e:
            log_error(f"Save language settings error: {e}")


# ── Intents Panel ─────────────────────────────────────────────

class IntentsPanel(QWidget):
    """Intent management panel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(PanelTitle("Intent Settings"))

        # Add new intent
        add_layout = QHBoxLayout()
        self._intent_name = QLineEdit()
        self._intent_name.setPlaceholderText("Intent name (e.g., open_spotify)")
        self._intent_name.setFixedHeight(40)
        self._intent_name.setStyleSheet(self._input_style())
        add_layout.addWidget(self._intent_name)

        add_btn = QPushButton("+ Add")
        add_btn.setFixedSize(70, 40)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {C['accent']};
                border: none;
                border-radius: 8px;
                color: #0D1117;
                font-size: 13px;
                font-weight: bold;
            }}
            QPushButton:hover {{ background-color: #00AACC; }}
        """)
        add_btn.clicked.connect(self._add_intent)
        add_layout.addWidget(add_btn)
        layout.addLayout(add_layout)

        # Examples input
        self._examples_input = QTextEdit()
        self._examples_input.setPlaceholderText(
            "Enter examples (one per line):\nopen spotify\nlaunch spotify\nplay spotify"
        )
        self._examples_input.setFixedHeight(90)
        self._examples_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['text']};
                font-size: 12px;
                font-family: 'Segoe UI';
                padding: 8px;
            }}
            QTextEdit:focus {{ border-color: {C['accent']}; }}
        """)
        layout.addWidget(self._examples_input)

        # Status
        self._status = QLabel("")
        self._status.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 12px;
            background: transparent; border: none; }}
        """)
        layout.addWidget(self._status)

        # Intent list
        list_header = QHBoxLayout()
        list_label = QLabel("Existing Intents")
        list_label.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            font-weight: bold; letter-spacing: 1px;
            background: transparent; border: none; }}
        """)
        list_header.addWidget(list_label)

        refresh_btn = QPushButton("↻ Refresh")
        refresh_btn.setFixedHeight(26)
        refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        refresh_btn.setStyleSheet(f"""
            QPushButton {{
                background: transparent;
                border: 1px solid {C['border']};
                border-radius: 4px;
                color: {C['subtext']};
                font-size: 11px;
                padding: 0 8px;
            }}
            QPushButton:hover {{ color: {C['accent']}; border-color: {C['accent']}; }}
        """)
        refresh_btn.clicked.connect(self._load_intents)
        list_header.addWidget(refresh_btn)
        layout.addLayout(list_header)

        self._intents_list = QListWidget()
        self._intents_list.setStyleSheet(f"""
            QListWidget {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['text']};
                font-size: 12px;
                font-family: 'Segoe UI';
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {C['border']};
            }}
            QListWidget::item:selected {{
                background-color: {C['surface2']};
                color: {C['accent']};
            }}
            QListWidget::item:hover {{
                background-color: {C['surface2']};
            }}
        """)
        layout.addWidget(self._intents_list)
        self._load_intents()

    def _input_style(self):
        return f"""
            QLineEdit {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 8px;
                color: {C['text']};
                font-size: 13px;
                font-family: 'Segoe UI';
                padding: 0 12px;
            }}
            QLineEdit:focus {{ border-color: {C['accent']}; }}
        """

    def _add_intent(self):
        intent_name = self._intent_name.text().strip().replace(' ', '_').lower()
        examples_text = self._examples_input.toPlainText().strip()

        if not intent_name:
            self._status.setText("❌ Enter an intent name")
            return

        examples = [
            e.strip() for e in examples_text.split('\n')
            if e.strip()
        ]
        if not examples:
            self._status.setText("❌ Add at least one example")
            return

        try:
            from NLP.nlp.intent_pipeline import get_intent_pipeline
            pipeline = get_intent_pipeline()
            success, message = pipeline.add_custom_intent(
                intent_name, examples
            )

            if success:
                self._status.setText(f"✅ Intent '{intent_name}' added")
                self._status.setStyleSheet(f"""
                    QLabel {{ color: {C['success']}; font-size: 12px;
                    background: transparent; border: none; }}
                """)
                self._intent_name.clear()
                self._examples_input.clear()
                self._load_intents()
            else:
                self._status.setText(f"❌ {message}")
        except Exception as e:
            log_error(f"Add intent error: {e}")
            self._status.setText(f"❌ Error: {e}")

    def _load_intents(self):
        try:
            from NLP.nlp.intent_pipeline import get_intent_pipeline
            pipeline = get_intent_pipeline()
            all_intents = pipeline.get_all_intents_with_examples()

            self._intents_list.clear()
            for intent, examples in sorted(all_intents.items()):
                item = QListWidgetItem(
                    f"  {intent}  ({len(examples)} examples)"
                )
                self._intents_list.addItem(item)
        except Exception as e:
            log_error(f"Load intents error: {e}")


# ── Security Panel ────────────────────────────────────────────

class SecurityPanel(QWidget):
    """Security settings panel"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(PanelTitle("Security Settings"))

        # Re-register face
        face_frame = QFrame()
        face_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        face_layout = QHBoxLayout(face_frame)
        face_layout.setContentsMargins(14, 10, 14, 10)

        face_info = QVBoxLayout()
        QLabel_style = f"""
            QLabel {{ color: {C['text']}; font-size: 13px;
            background: transparent; border: none; }}
        """
        face_title = QLabel("👤 Face Recognition")
        face_title.setStyleSheet(QLabel_style)
        face_info.addWidget(face_title)
        face_sub = QLabel("Update your face data")
        face_sub.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            background: transparent; border: none; }}
        """)
        face_info.addWidget(face_sub)
        face_layout.addLayout(face_info)
        face_layout.addStretch()

        re_register_face_btn = QPushButton("Re-register")
        re_register_face_btn.setFixedSize(100, 34)
        re_register_face_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        re_register_face_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {C['accent']};
                border-radius: 6px;
                color: {C['accent']};
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #0D2030; }}
        """)
        re_register_face_btn.clicked.connect(self._re_register_face)
        face_layout.addWidget(re_register_face_btn)
        layout.addWidget(face_frame)

        # Re-register voice password
        voice_frame = QFrame()
        voice_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        voice_layout = QHBoxLayout(voice_frame)
        voice_layout.setContentsMargins(14, 10, 14, 10)

        voice_info = QVBoxLayout()
        voice_title = QLabel("🎤 Voice Password")
        voice_title.setStyleSheet(QLabel_style)
        voice_info.addWidget(voice_title)
        voice_sub = QLabel("Update your voice passphrase")
        voice_sub.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            background: transparent; border: none; }}
        """)
        voice_info.addWidget(voice_sub)
        voice_layout.addLayout(voice_info)
        voice_layout.addStretch()

        re_voice_btn = QPushButton("Re-register")
        re_voice_btn.setFixedSize(100, 34)
        re_voice_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        re_voice_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {C['accent']};
                border-radius: 6px;
                color: {C['accent']};
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #0D2030; }}
        """)
        re_voice_btn.clicked.connect(self._re_register_voice)
        voice_layout.addWidget(re_voice_btn)
        layout.addWidget(voice_frame)

        # Add speaker sample
        speaker_frame = QFrame()
        speaker_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        speaker_layout = QHBoxLayout(speaker_frame)
        speaker_layout.setContentsMargins(14, 10, 14, 10)

        speaker_info = QVBoxLayout()
        speaker_title = QLabel("🔊 Speaker Profile")
        speaker_title.setStyleSheet(QLabel_style)
        speaker_info.addWidget(speaker_title)
        speaker_sub = QLabel("Add more voice samples")
        speaker_sub.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            background: transparent; border: none; }}
        """)
        speaker_info.addWidget(speaker_sub)
        speaker_layout.addLayout(speaker_info)
        speaker_layout.addStretch()

        add_sample_btn = QPushButton("Add Sample")
        add_sample_btn.setFixedSize(100, 34)
        add_sample_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_sample_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {C['accent']};
                border-radius: 6px;
                color: {C['accent']};
                font-size: 12px;
            }}
            QPushButton:hover {{ background-color: #0D2030; }}
        """)
        add_sample_btn.clicked.connect(self._add_speaker_sample)
        speaker_layout.addWidget(add_sample_btn)
        layout.addWidget(speaker_frame)

        self._status = QLabel("")
        self._status.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 12px;
            background: transparent; border: none; }}
        """)
        layout.addWidget(self._status)
        layout.addStretch()

    def set_user(self, username):
        self._username = username

    def _re_register_face(self):
        self._status.setText("📷 Opening camera for face registration...")
        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            import threading
            auth = get_auth_orchestrator()

            def run():
                success, message = auth.re_register_face(self._username)
                status = "✅ Face re-registered" if success else f"❌ {message}"
                self._status.setText(status)

            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            log_error(f"Re-register face error: {e}")

    def _re_register_voice(self):
        self._status.setText("🎤 Recording new voice password...")
        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            import threading
            auth = get_auth_orchestrator()

            def run():
                success, message = auth.re_register_voice_password(
                    self._username, "hey deskmate"
                )
                status = "✅ Voice re-registered" if success else f"❌ {message}"
                self._status.setText(status)

            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            log_error(f"Re-register voice error: {e}")

    def _add_speaker_sample(self):
        self._status.setText("🎤 Recording speaker sample...")
        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            import threading
            auth = get_auth_orchestrator()

            def run():
                success, message = auth.add_speaker_sample(self._username)
                status = "✅ Sample added" if success else f"❌ {message}"
                self._status.setText(status)

            threading.Thread(target=run, daemon=True).start()
        except Exception as e:
            log_error(f"Add speaker sample error: {e}")


# ── Users Panel ───────────────────────────────────────────────

class UsersPanel(QWidget):
    """Users management panel (admin only)"""

    add_user_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._admin_username = ""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        layout.addWidget(PanelTitle("User Management"))

        # Add user button
        add_btn = SettingsButton("➕  Add New User", primary=True)
        add_btn.clicked.connect(self.add_user_requested.emit)
        layout.addWidget(add_btn)

        # Users list
        users_header = QLabel("REGISTERED USERS")
        users_header.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            font-weight: bold; letter-spacing: 1px;
            background: transparent; border: none; }}
        """)
        layout.addWidget(users_header)

        self._users_container = QVBoxLayout()
        self._users_container.setSpacing(8)

        users_frame = QFrame()
        users_frame.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border: 1px solid {C['border']};
                border-radius: 10px;
            }}
        """)
        users_frame_layout = QVBoxLayout(users_frame)
        users_frame_layout.setContentsMargins(12, 12, 12, 12)
        users_frame_layout.setSpacing(8)

        self._users_frame_layout = users_frame_layout
        layout.addWidget(users_frame)

        refresh_btn = SettingsButton("↻  Refresh Users")
        refresh_btn.clicked.connect(self._load_users)
        layout.addWidget(refresh_btn)

        layout.addStretch()
        self._load_users()

    def set_admin(self, username):
        self._admin_username = username
        self._load_users()

    def _load_users(self):
        while self._users_frame_layout.count():
            item = self._users_frame_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        try:
            from backend.security.registration import get_registration_manager
            reg = get_registration_manager()
            users = reg.get_all_users()

            for user in users:
                row = self._create_user_row(user)
                self._users_frame_layout.addWidget(row)

            if not users:
                empty = QLabel("No users registered")
                empty.setStyleSheet(f"""
                    QLabel {{ color: {C['subtext']}; font-size: 12px;
                    padding: 8px; background: transparent; border: none; }}
                """)
                self._users_frame_layout.addWidget(empty)

        except Exception as e:
            log_error(f"Load users error: {e}")

    def _create_user_row(self, user_info):
        row = QFrame()
        row.setFixedHeight(44)
        row.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface2']};
                border: 1px solid {C['border']};
                border-radius: 8px;
            }}
        """)
        row_layout = QHBoxLayout(row)
        row_layout.setContentsMargins(12, 0, 12, 0)

        avatar = QLabel(user_info['username'][0].upper())
        avatar.setFixedSize(28, 28)
        avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {C['surface']};
                border: 1px solid {C['accent']};
                border-radius: 14px;
                color: {C['accent']};
                font-size: 13px;
                font-weight: bold;
            }}
        """)
        row_layout.addWidget(avatar)

        name = QLabel(user_info['username'])
        name.setStyleSheet(f"""
            QLabel {{ color: {C['text']}; font-size: 13px;
            background: transparent; border: none; }}
        """)
        row_layout.addWidget(name)

        if user_info.get('is_admin'):
            admin_tag = QLabel("Admin")
            admin_tag.setStyleSheet(f"""
                QLabel {{
                    background-color: #1C2E3A;
                    color: {C['accent']};
                    font-size: 10px;
                    border-radius: 4px;
                    padding: 2px 6px;
                    border: none;
                }}
            """)
            row_layout.addWidget(admin_tag)

        row_layout.addStretch()

        username = user_info['username']
        if username != self._admin_username:
            del_btn = QPushButton("Remove")
            del_btn.setFixedSize(70, 26)
            del_btn.setCursor(Qt.CursorShape.PointingHandCursor)
            del_btn.setStyleSheet(f"""
                QPushButton {{
                    background: transparent;
                    border: 1px solid {C['error']};
                    border-radius: 4px;
                    color: {C['error']};
                    font-size: 11px;
                }}
                QPushButton:hover {{ background-color: #1A0D0D; }}
            """)
            del_btn.clicked.connect(
                lambda checked, u=username: self._remove_user(u)
            )
            row_layout.addWidget(del_btn)

        return row

    def _remove_user(self, username):
        # print(f"[USERS] Remove: {username}")
        try:
            from PyQt6.QtWidgets import QInputDialog
            password, ok = QInputDialog.getText(
                self,
                "Admin Verification",
                "Enter admin password to remove user:",
                QLineEdit.EchoMode.Password
            )
            if ok and password:
                from backend.security.auth_orchestrator import get_auth_orchestrator
                auth = get_auth_orchestrator()
                success, message = auth.delete_user(
                    self._admin_username, password, username
                )
                if success:
                    self._load_users()
        except Exception as e:
            log_error(f"Remove user error: {e}")


# ── Settings Window ───────────────────────────────────────────

class SettingsWindow(QWidget):
    """
    Main settings window
    Matches Image 4 two-panel design exactly
    """

    language_changed = pyqtSignal(str, str)
    wake_word_changed = pyqtSignal(str, float)
    add_user_requested = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._username = ""
        self._is_admin = False

        self._setup_window()
        self._setup_ui()

        log_info("SettingsWindow initialized")

    def _setup_window(self):
        self.setWindowTitle("DeskmateAI - Settings")
        self.setFixedSize(700, 520)
        self.setWindowFlags(
            Qt.WindowType.Window |
            Qt.WindowType.WindowCloseButtonHint
        )
        self.setStyleSheet(f"QWidget {{ background-color: {C['bg']}; }}")

    def _setup_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ── Left Sidebar ───────────────────────────────────
        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {C['sidebar']};
                border-right: 1px solid {C['border']};
            }}
        """)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        # Sidebar header
        sidebar_header = QFrame()
        sidebar_header.setFixedHeight(70)
        sidebar_header.setStyleSheet(f"""
            QFrame {{
                background-color: {C['surface']};
                border-bottom: 1px solid {C['border']};
            }}
        """)
        sh_layout = QVBoxLayout(sidebar_header)
        sh_layout.setContentsMargins(16, 0, 16, 0)

        sh_title = QLabel("DeskmateAI")
        sh_title.setStyleSheet(f"""
            QLabel {{ color: {C['text']}; font-size: 15px;
            font-weight: bold; background: transparent; border: none; }}
        """)
        sh_layout.addWidget(sh_title)

        sh_sub = QLabel("Voice Assistant")
        sh_sub.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            background: transparent; border: none; }}
        """)
        sh_layout.addWidget(sh_sub)

        sidebar_layout.addWidget(sidebar_header)

        # Nav items
        nav_items = [
            ("👤", "Profile", 0),
            ("🌐", "Language", 1),
            ("🎤", "Wake Word", 1),
            ("🧠", "Intents", 2),
            ("🔐", "Security", 3),
            ("👥", "Users", 4),
        ]

        self._nav_buttons = []
        self._button_group = QButtonGroup(self)

        for icon, text, panel_idx in nav_items:
            btn = NavItem(icon, text)
            btn.clicked.connect(
                lambda checked, idx=panel_idx: self._switch_panel(idx)
            )
            self._button_group.addButton(btn)
            self._nav_buttons.append(btn)
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        # Version
        version = QLabel("v1.0.0")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        version.setStyleSheet(f"""
            QLabel {{ color: {C['subtext']}; font-size: 11px;
            padding: 8px; background: transparent; border: none; }}
        """)
        sidebar_layout.addWidget(version)

        main_layout.addWidget(sidebar)

        # ── Right Content ──────────────────────────────────
        content_area = QFrame()
        content_area.setStyleSheet(f"""
            QFrame {{
                background-color: {C['bg']};
                border: none;
            }}
        """)

        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(28, 24, 28, 24)

        self._stack = QStackedWidget()
        self._stack.setStyleSheet("QStackedWidget { background: transparent; }")

        # Create panels
        self._profile_panel = ProfilePanel()
        self._language_panel = LanguagePanel()
        self._intents_panel = IntentsPanel()
        self._security_panel = SecurityPanel()
        self._users_panel = UsersPanel()

        self._stack.addWidget(self._profile_panel)    # 0
        self._stack.addWidget(self._language_panel)   # 1
        self._stack.addWidget(self._intents_panel)    # 2
        self._stack.addWidget(self._security_panel)   # 3
        self._stack.addWidget(self._users_panel)      # 4

        # Connect signals
        self._language_panel.language_changed.connect(
            self.language_changed.emit
        )
        self._language_panel.wake_word_changed.connect(
            self.wake_word_changed.emit
        )
        self._users_panel.add_user_requested.connect(
            self.add_user_requested.emit
        )

        content_layout.addWidget(self._stack)
        main_layout.addWidget(content_area)

        # Select first nav item
        if self._nav_buttons:
            self._nav_buttons[0].setChecked(True)

    def _switch_panel(self, index):
        """Switch content panel"""
        # print(f"[SETTINGS] Panel: {index}")
        self._stack.setCurrentIndex(index)

    def set_user(self, username, is_admin, profile):
        """Initialize with user data"""
        # print(f"[SETTINGS] User: {username}")
        self._username = username
        self._is_admin = is_admin

        self._profile_panel.set_user(username, is_admin)
        self._language_panel.set_user(username, profile)
        self._security_panel.set_user(username)

        if is_admin:
            self._users_panel.set_admin(username)

        # Show/hide Users nav item
        for btn in self._nav_buttons:
            if "Users" in btn.text():
                btn.setVisible(is_admin)