# DeskmateAI/ui/controller.py

import os
import sys
import threading
from PyQt6.QtWidgets import QApplication, QWidget
from PyQt6.QtCore import QObject, pyqtSignal, QTimer, Qt, QThread

# ============================================================
# UI CONTROLLER FOR DESKMATEAI
# Central bridge between UI and backend pipeline
# Manages:
# - Window lifecycle (login, register, dashboard, settings)
# - Tray icon state updates
# - Pipeline callbacks → UI updates
# - User session management
# - Voice login coordination
# All UI updates happen on main thread via signals
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR)

from backend.utils.logger import log_info, log_error, log_debug, log_warning

# ── Pipeline Worker Thread ────────────────────────────────────

class PipelineWorker(QThread):
    """
    Runs pipeline in background thread
    Emits signals to update UI safely
    """
    # UI update signals
    status_changed = pyqtSignal(str)           # idle/listening/processing
    transcription_ready = pyqtSignal(str)      # transcribed text
    intent_classified = pyqtSignal(str, float, str)  # intent, score, source
    command_executed = pyqtSignal(str, bool, str)    # intent, success, entity
    wake_word_detected = pyqtSignal()
    dictation_mode = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    audio_level = pyqtSignal(float)

    def __init__(self, user_profile, parent=None):
        super().__init__(parent)
        self._profile = user_profile
        self._running = False
        self._pipeline = None
        # print("[PIPELINE_WORKER] Initialized")

    def run(self):
        """Start pipeline in background"""
        # print("[PIPELINE_WORKER] Starting pipeline...")
        self._running = True

        try:
            from backend.core.pipeline import get_pipeline
            self._pipeline = get_pipeline()

            # Register callbacks
            self._pipeline.register_callbacks({
                'on_wake_word_detected': self._on_wake_word,
                'on_listening_start': self._on_listening_start,
                'on_listening_end': self._on_listening_end,
                'on_processing_start': self._on_processing_start,
                'on_processing_end': self._on_processing_end,
                'on_transcription': self._on_transcription,
                'on_intent_classified': self._on_intent,
                'on_command_executed': self._on_command_executed,
                'on_error': self._on_error,
                'on_status_change': self._on_status,
                'on_dictation_mode': self._on_dictation,
            })

            # Start pipeline
            success = self._pipeline.start(self._profile)
            if not success:
                self.error_occurred.emit("Failed to start pipeline")
                return

            # print("[PIPELINE_WORKER] ✅ Pipeline started")
            log_info("Pipeline worker started")

            # Keep thread alive
            while self._running:
                self.msleep(100)

        except Exception as e:
            # print(f"[PIPELINE_WORKER] Error: {e}")
            log_error(f"Pipeline worker error: {e}")
            self.error_occurred.emit(str(e))

    def stop(self):
        """Stop pipeline"""
        # print("[PIPELINE_WORKER] Stopping...")
        self._running = False
        if self._pipeline:
            self._pipeline.stop()
        log_info("Pipeline worker stopped")

    # ── Pipeline Callbacks ────────────────────────────────────

    def _on_wake_word(self):
        # print("[PIPELINE_WORKER] Wake word detected")
        self.wake_word_detected.emit()
        self.status_changed.emit("wakeword")

    def _on_listening_start(self):
        # print("[PIPELINE_WORKER] Listening start")
        self.status_changed.emit("listening")

    def _on_listening_end(self):
        pass

    def _on_processing_start(self):
        # print("[PIPELINE_WORKER] Processing start")
        self.status_changed.emit("processing")

    def _on_processing_end(self, success):
        pass

    def _on_transcription(self, text):
        # print(f"[PIPELINE_WORKER] Transcription: {text}")
        self.transcription_ready.emit(text)

    def _on_intent(self, intent, score, source):
        # print(f"[PIPELINE_WORKER] Intent: {intent} ({score:.2f})")
        self.intent_classified.emit(intent, score, source)

    def _on_command_executed(self, intent, success, entity):
        # print(f"[PIPELINE_WORKER] Command: {intent} | success={success}")
        self.command_executed.emit(
            intent, success, entity or ""
        )
        self.status_changed.emit("success" if success else "error")

    def _on_error(self, error):
        # print(f"[PIPELINE_WORKER] Error: {error}")
        self.error_occurred.emit(error)
        self.status_changed.emit("error")

    def _on_status(self, status):
        self.status_changed.emit(status)

    def _on_dictation(self, active):
        self.dictation_mode.emit(active)


# ── Audio Level Worker ────────────────────────────────────────

class AudioLevelWorker(QThread):
    """Streams audio levels for waveform animation"""
    import os, time
    os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
    os.environ['OMP_NUM_THREADS'] = '1'
    time.sleep(5)
    level_updated = pyqtSignal(float)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._running = False
        self._stop_event = threading.Event()

    def run(self):
        self._running = True
        self._stop_event.clear()

        try:
            from NLP.speech.asr.speech_handler import get_speech_handler
            handler = get_speech_handler()
            handler.stream_audio_levels(
                callback=self.level_updated.emit,
                stop_event=self._stop_event
            )
        except Exception as e:
            # print(f"[AUDIO_LEVEL] Error: {e}")
            log_error(f"Audio level worker error: {e}")

    def stop(self):
        self._running = False
        self._stop_event.set()

class SpeechWarmupThread(QThread):
    """Pre-loads Resemblyzer VoiceEncoder in background at startup.
    Prevents first-load crash when Step 3 registration fires."""

    def run(self):
        try:
            import os
            os.environ['KMP_DUPLICATE_LIB_OK'] = 'TRUE'
            os.environ['OMP_NUM_THREADS'] = '1'
            os.environ['OPENBLAS_NUM_THREADS'] = '1'
            os.environ['MKL_NUM_THREADS'] = '1'
            from backend.security.speech_auth import get_speech_auth
            get_speech_auth()
        except Exception:
            pass  # non-fatal — step 3 will retry if needed

# ── UI Controller ─────────────────────────────────────────────

class UIController(QObject):
    """
    Central UI controller
    Manages all windows and connects them to backend
    """

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._current_user = None
        self._current_profile = None
        self._is_admin = False

        # Windows
        self._login_window = None
        self._register_window = None
        self._main_window = None
        self._dashboard_window = None
        self._settings_window = None
        self._tray_icon = None

        # Workers
        self._pipeline_worker = None
        self._audio_worker = None
        self._speech_warmup = None  
        log_info("UIController initialized")
        # print("[CONTROLLER] UIController initialized")

    # ── Startup ───────────────────────────────────────────────

    def start(self):
        """Start the application"""
        # print("[CONTROLLER] Starting application...")
        log_info("Application starting")

        self._setup_tray()
        #self._start_speech_warmup()
        self._check_first_run()
        print("DEBUG: UIController.start() called")

    def _start_speech_warmup(self):
        """Pre-warm Resemblyzer in background so Step 3 doesn't crash"""
        self._speech_warmup = SpeechWarmupThread(self)
        self._speech_warmup.start()
    
    def _setup_tray(self):
        """Initialize system tray icon"""
        # print("[CONTROLLER] Setting up tray...")
        from ui.tray_icon import TrayIconManager

        self._tray_icon = TrayIconManager(self._app)
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(0, self._tray_icon.show)

        # Connect tray signals
        self._tray_icon.show_dashboard.connect(self._show_dashboard)
        self._tray_icon.show_settings.connect(self._show_settings)
        self._tray_icon.add_new_user.connect(self._show_add_user)
        self._tray_icon.switch_user.connect(self._show_login)
        self._tray_icon.logout_requested.connect(self._logout)
        self._tray_icon.exit_requested.connect(self._exit_app)
        self._tray_icon.mute_toggled.connect(self._on_mute_toggled)

        self._tray_icon.update_tooltip("DeskmateAI — Starting...")
        # print("[CONTROLLER] ✅ Tray setup complete")

    def _check_first_run(self):
        """Check if first run and show appropriate window"""
        # print("[CONTROLLER] Checking first run...")
        try:
            from backend.security.registration import get_registration_manager
            reg = get_registration_manager()

            if reg.is_first_run():
                # print("[CONTROLLER] First run — showing registration")
                log_info("First run — showing registration")
                self._show_register(first_run=True)
            else:
                # print("[CONTROLLER] Existing users — showing login")
                log_info("Existing users — showing login")
                self._show_login()

        except Exception as e:
            # print(f"[CONTROLLER] First run check error: {e}")
            log_error(f"First run check error: {e}")
            self._show_login()

    # ── Login ─────────────────────────────────────────────────

    def _show_login(self):
        """Show login window"""
        # print("[CONTROLLER] Showing login...")
        log_info("Showing login window")

        if self._audio_worker and self._audio_worker.isRunning():
            self._audio_worker.stop()
            self._audio_worker.quit()
            self._audio_worker.wait(2000)
            self._audio_worker = None
        
        if self._login_window:
            self._login_window.close()

        from ui.views.login_window import LoginWindow
        self._login_window = LoginWindow()
        self._login_window.login_success.connect(self._on_login_success)
        self._login_window.register_requested.connect(
            lambda: self._show_register(first_run=False)
        )
        self._login_window.show()

    def _on_login_success(self, username, method, profile):
        """Handle successful login"""
        # print(f"[CONTROLLER] Login success: {username}")
        log_info(f"Login success: {username} via {method}")

        self._current_user = username
        self._current_profile = profile
        self._is_admin = profile.get('is_admin', False)

        # Close login window
        if self._login_window:
            self._login_window.close()
            self._login_window = None

        # Update tray
        self._tray_icon.set_user(username, self._is_admin)
        self._tray_icon.update_tooltip(f"DeskmateAI — {username}")

        # Start pipeline
        self._start_pipeline(profile)

        # Show notification
        self._tray_icon.show_notification(
            "DeskmateAI",
            f"Welcome back, {username}! 👋",
            duration=3000
        )

        # Setup floating window
        self._setup_main_window()

        # print(f"[CONTROLLER] ✅ Session started: {username}")

    # ── Register ──────────────────────────────────────────────

    def _show_register(self, first_run=False):
        """Show registration window"""
        # print(f"[CONTROLLER] Showing register (first_run={first_run})...")
        log_info(f"Showing registration (first_run={first_run})")

        from ui.views.register_window import RegisterWindow
        self._register_window = RegisterWindow(
            admin_mode=not first_run
        )
        self._register_window.registration_complete.connect(
            self._on_registration_complete
        )
        self._register_window.back_to_login.connect(
            lambda: (
                self._register_window.close(),
                self._show_login() if not first_run else None
            )
        )
        self._register_window.show()

    def _on_registration_complete(self, username):
        """Handle registration completion"""
        # print(f"[CONTROLLER] Registration complete: {username}")
        log_info(f"Registration complete: {username}")

        if self._register_window:
            self._register_window.close()
            self._register_window = None

        # Show login
        QTimer.singleShot(3000, self._show_login)

    def _show_add_user(self):
        """Show add user (admin authorization required)"""
        # print("[CONTROLLER] Add user requested...")
        if not self._is_admin:
            log_warning("Non-admin tried to add user")
            return

        from ui.views.register_window import RegisterWindow
        self._register_window = RegisterWindow(admin_mode=True)
        self._register_window.registration_complete.connect(
            lambda u: (
                self._register_window.close(),
                self._tray_icon.show_notification(
                    "DeskmateAI",
                    f"User '{u}' added successfully!"
                )
            )
        )
        self._register_window.back_to_login.connect(
            lambda: self._register_window.close()
        )
        self._register_window.show()

    # ── Pipeline ──────────────────────────────────────────────
    def stop_audio_stream(self):
        """Stop audio level worker to prevent mic conflict"""
        if self._audio_worker and self._audio_worker.isRunning():
            print("[FIX] Stopping audio worker before recording...")
            self._audio_worker.stop()
            self._audio_worker.quit()
            self._audio_worker.wait()
        
    def _start_pipeline(self, profile):
        """Start voice assistant pipeline"""
        # print("[CONTROLLER] Starting pipeline...")
        log_info("Starting pipeline worker")

        # Stop existing
        if self._pipeline_worker and self._pipeline_worker.isRunning():
            self._pipeline_worker.stop()
            self._pipeline_worker.quit()

        # Start new pipeline worker
        self._pipeline_worker = PipelineWorker(profile)

        # Connect signals
        self._pipeline_worker.status_changed.connect(self._on_status_change)
        self._pipeline_worker.transcription_ready.connect(self._on_transcription)
        self._pipeline_worker.intent_classified.connect(self._on_intent)
        self._pipeline_worker.command_executed.connect(self._on_command_executed)
        self._pipeline_worker.wake_word_detected.connect(self._on_wake_word)
        self._pipeline_worker.dictation_mode.connect(self._on_dictation_mode)
        self._pipeline_worker.error_occurred.connect(self._on_pipeline_error)
        self._pipeline_worker.audio_level.connect(self._on_audio_level)

        self._pipeline_worker.start()
        # print("[CONTROLLER] ✅ Pipeline worker started")

        # Start audio level worker
        self._start_audio_worker()

    def _start_audio_worker(self):
        """Start audio level streaming"""
        # print("[CONTROLLER] Starting audio level worker...")
        if self._audio_worker and self._audio_worker.isRunning():
            self._audio_worker.stop()

        self._audio_worker = AudioLevelWorker()
        self._audio_worker.level_updated.connect(self._on_audio_level)
        self._audio_worker.start()

    def _stop_pipeline(self):
        """Stop pipeline and audio worker"""
        # print("[CONTROLLER] Stopping pipeline...")
        if self._pipeline_worker:
            self._pipeline_worker.stop()
            self._pipeline_worker.quit()
            self._pipeline_worker = None

        if self._audio_worker:
            self._audio_worker.stop()
            self._audio_worker.quit()
            self._audio_worker = None

        log_info("Pipeline stopped")

    # ── Pipeline Callbacks → UI ───────────────────────────────

    def _on_status_change(self, status):
        """Update UI with new status"""
        # print(f"[CONTROLLER] Status: {status}")

        # Update tray icon
        from ui.tray_icon import IconState
        state_map = {
            "idle":       IconState.IDLE,
            "wakeword":   IconState.WAKEWORD,
            "listening":  IconState.LISTENING,
            "processing": IconState.PROCESSING,
            "executing":  IconState.PROCESSING,
            "success":    IconState.SUCCESS,
            "error":      IconState.ERROR,
        }
        icon_state = state_map.get(status, IconState.IDLE)
        self._tray_icon.set_state(icon_state)

        # Update floating window if visible
        if self._main_window and self._main_window.isVisible():
            self._main_window.set_status(status)

    def _on_wake_word(self):
        """Handle wake word detection"""
        # print("[CONTROLLER] Wake word detected")
        # Icon animates — NO window opens
        # Window only opens if user asks for it

    def _on_transcription(self, text):
        """Update transcription in floating window"""
        # print(f"[CONTROLLER] Transcription: {text}")
        if self._main_window and self._main_window.isVisible():
            self._main_window.set_transcription(text)

    def _on_intent(self, intent, score, source):
        """Handle intent classification"""
        # print(f"[CONTROLLER] Intent: {intent} ({score:.2f}) [{source}]")
        log_debug(f"Intent: {intent} ({score:.2f}) [{source}]")

        # Check for UI commands
        self._handle_ui_commands(intent)

    def _handle_ui_commands(self, intent):
        """Handle intents that control UI"""
        # print(f"[CONTROLLER] UI command check: {intent}")
        ui_commands = {
            "open_dashboard": self._show_dashboard,
            "show_dashboard": self._show_dashboard,
            "open_settings":  self._show_settings,
            "hide_window":    self._hide_main_window,
            "close_window":   self._hide_main_window,
        }
        if intent in ui_commands:
            QTimer.singleShot(0, ui_commands[intent])

    def _on_command_executed(self, intent, success, entity):
        """Handle command execution result"""
        # print(f"[CONTROLLER] Command: {intent} | success={success}")
        log_debug(f"Command executed: {intent} | {success}")

        # Update floating window
        if self._main_window and self._main_window.isVisible():
            self._main_window.on_command_complete(intent, success, entity)

        # Update dashboard history
        if self._dashboard_window:
            from datetime import datetime
            time_str = datetime.now().strftime("%I:%M %p")
            try:
                self._dashboard_window.add_command(
                    intent.replace('_', ' ').title(),
                    intent,
                    success,
                    time_str
            )
            except RuntimeError:
                pass 

    def _on_audio_level(self, level):
        """Update waveform with audio level"""
        if self._main_window and self._main_window.isVisible():
            self._main_window.set_audio_level(level)

    def _on_dictation_mode(self, active):
        """Handle dictation mode change"""
        # print(f"[CONTROLLER] Dictation mode: {active}")
        if active and self._main_window:
            self._main_window.show_window()
            self._main_window.set_status("listening")

    def _on_pipeline_error(self, error):
        """Handle pipeline error"""
        # print(f"[CONTROLLER] Pipeline error: {error}")
        log_error(f"Pipeline error: {error}")
        self._tray_icon.show_notification(
            "DeskmateAI Error",
            error,
            icon=__import__('PyQt6.QtWidgets', fromlist=['QSystemTrayIcon']).QSystemTrayIcon.MessageIcon.Warning
        )

    def _on_mute_toggled(self, muted):
        """Handle mute toggle"""
        # print(f"[CONTROLLER] Muted: {muted}")
        log_info(f"Assistant muted: {muted}")
        if self._pipeline_worker and self._pipeline_worker._pipeline:
            pass  # Pipeline handles mute internally

    # ── Window Management ─────────────────────────────────────

    def _setup_main_window(self):
        """Setup floating command window"""
        # print("[CONTROLLER] Setting up main window...")
        from ui.views.main_window import MainWindow
        self._main_window = MainWindow()
        self._main_window.close_requested.connect(self._hide_main_window)
        self._main_window.open_dashboard.connect(self._show_dashboard)
        # print("[CONTROLLER] ✅ Main window ready (hidden)")

    def _hide_main_window(self):
        """Hide floating window"""
        # print("[CONTROLLER] Hiding main window...")
        if self._main_window:
            self._main_window.hide_window()

    def _show_dashboard(self):
        """Show dashboard window"""
        # print("[CONTROLLER] Showing dashboard...")
        log_info("Showing dashboard")

        if not self._dashboard_window:
            from ui.views.dashboard_window import DashboardWindow
            self._dashboard_window = DashboardWindow()
            self._dashboard_window.settings_requested.connect(
                self._show_settings
            )
            self._dashboard_window.logout_requested.connect(self._logout)
            self._dashboard_window.exit_requested.connect(self._exit_app)

        if self._current_user:
            self._dashboard_window.set_user(
                self._current_user, self._is_admin
            )

        self._dashboard_window.show()

    def _show_settings(self):
        """Show settings window"""
        # print("[CONTROLLER] Showing settings...")
        log_info("Showing settings")

        if not self._settings_window:
            from ui.views.settings_window import SettingsWindow
            self._settings_window = SettingsWindow()
            self._settings_window.language_changed.connect(
                self._on_language_changed
            )
            self._settings_window.wake_word_changed.connect(
                self._on_wake_word_changed
            )
            self._settings_window.add_user_requested.connect(
                self._show_add_user
            )

        if self._current_user and self._current_profile:
            self._settings_window.set_user(
                self._current_user,
                self._is_admin,
                self._current_profile
            )

        self._settings_window.show()
        self._settings_window.raise_()

    def _on_language_changed(self, lang_code, lang_name):
        """Handle language change from settings"""
        # print(f"[CONTROLLER] Language: {lang_code}")
        log_info(f"Language changed: {lang_code}")
        if self._pipeline_worker and self._pipeline_worker._pipeline:
            self._pipeline_worker._pipeline.update_language(
                lang_code, lang_name
            )

    def _on_wake_word_changed(self, wake_word, sensitivity):
        """Handle wake word change from settings"""
        # print(f"[CONTROLLER] Wake word: {wake_word}")
        log_info(f"Wake word changed: {wake_word}")
        if self._pipeline_worker and self._pipeline_worker._pipeline:
            self._pipeline_worker._pipeline.update_wake_word(
                wake_word, sensitivity
            )

    # ── Logout / Exit ─────────────────────────────────────────

    def _logout(self):
        """Logout current user"""
        # print(f"[CONTROLLER] Logout: {self._current_user}")
        log_info(f"Logout: {self._current_user}")

        # Stop pipeline
        self._stop_pipeline()

        # End session
        try:
            from backend.security.auth_orchestrator import get_auth_orchestrator
            auth = get_auth_orchestrator()
            auth.logout()
        except Exception as e:
            log_error(f"Logout error: {e}")

        # Close windows
        if self._dashboard_window:
            self._dashboard_window.close()
            self._dashboard_window = None
        if self._settings_window:
            self._settings_window.close()
            self._settings_window = None
        if self._main_window:
            self._main_window.hide()
            self._main_window = None

        # Reset state
        self._current_user = None
        self._current_profile = None
        self._is_admin = False

        # Update tray
        self._tray_icon.set_user("", False)
        self._tray_icon.update_tooltip("DeskmateAI — Logged out")

        # Show login
        self._show_login()

    def _exit_app(self):
        """Exit application"""
        # print("[CONTROLLER] Exiting application...")
        log_info("Application exiting")

        self._stop_pipeline()

        if self._tray_icon:
            self._tray_icon.cleanup()

        # Close all windows
        for window in [
            self._login_window, self._register_window,
            self._main_window, self._dashboard_window,
            self._settings_window
        ]:
            if window:
                try:
                    window.close()
                except:
                    pass

        self._app.quit()