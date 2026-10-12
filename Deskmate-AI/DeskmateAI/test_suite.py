# DeskmateAI - Comprehensive Test Suite
# Tests every module for: import health, class instantiation, and core logic
# Does NOT require models, mic, GPU, or any external environment
# Run from the project root:  python test_suite.py
#
# Results: PASS / FAIL / SKIP with reason
# ============================================================

import os
import sys
import json
import traceback
import time

# ── Setup Root Path ──────────────────────────────────────────
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

# ── Terminal Colors ──────────────────────────────────────────
GREEN  = "\033[92m"
RED    = "\033[91m"
YELLOW = "\033[93m"
CYAN   = "\033[96m"
BOLD   = "\033[1m"
RESET  = "\033[0m"

# ── Result Tracking ──────────────────────────────────────────
results = []

def passed(name, detail=""):
    results.append(("PASS", name, detail))
    tag = f"{GREEN}{BOLD}[PASS]{RESET}"
    print(f"  {tag} {name}" + (f"  ->  {detail}" if detail else ""))

def failed(name, detail=""):
    results.append(("FAIL", name, detail))
    tag = f"{RED}{BOLD}[FAIL]{RESET}"
    print(f"  {tag} {name}" + (f"  ->  {detail}" if detail else ""))

def skipped(name, reason=""):
    results.append(("SKIP", name, reason))
    tag = f"{YELLOW}{BOLD}[SKIP]{RESET}"
    print(f"  {tag} {name}" + (f"  ->  {reason}" if reason else ""))

def section(title):
    print(f"\n{CYAN}{BOLD}{'─'*60}{RESET}")
    print(f"{CYAN}{BOLD}  {title}{RESET}")
    print(f"{CYAN}{BOLD}{'─'*60}{RESET}")


# ================================================================
# 1. UTILITY MODULES
# ================================================================

section("1. UTILITY MODULES")

# 1.1 Logger
try:
    from backend.utils.logger import (
        setup_logger, log_info, log_error, log_debug,
        log_warning, log_critical, log_action, log_auth,
        log_intent, log_wake_word, log_error_trace,
        get_log_file_path, clear_logs
    )
    setup_logger()
    log_info("Test info")
    log_debug("Test debug")
    log_warning("Test warning")
    log_error("Test error")
    log_critical("Test critical")
    log_action("user1", "open_app", "open chrome", True)
    log_auth("user1", "password", True)
    log_intent("open chrome", "open_app", 0.95, "sbert")
    log_wake_word("hey deskmate", "hey deskmate")
    log_error_trace("Test trace", Exception("test"))
    assert isinstance(get_log_file_path(), str)
    passed("backend.utils.logger", "All 11 log functions callable with correct signatures")
except Exception as e:
    failed("backend.utils.logger", str(e))

# 1.2 Utils
try:
    from backend.utils.utils import (
        get_base_dir, get_backend_dir, get_data_dir,
        get_users_dir, get_user_dir, get_nlp_dir,
        get_models_dir, get_whisper_model_dir,
        get_translation_model_dir, get_intents_dir,
        get_intent_examples_path, get_intent_memory_path,
        get_profile_path, list_users, ensure_dir,
        load_json, save_json, get_timestamp
    )
    assert isinstance(get_base_dir(), str)
    assert isinstance(get_whisper_model_dir(), str)
    assert isinstance(get_intents_dir(), str)
    ts = get_timestamp()
    assert isinstance(ts, str) and len(ts) > 0

    test_dir = os.path.join(BASE_DIR, "backend", "data", "_test_ensure")
    ensure_dir(test_dir)
    assert os.path.exists(test_dir)
    os.rmdir(test_dir)

    test_json = os.path.join(BASE_DIR, "backend", "data", "_test.json")
    ensure_dir(os.path.dirname(test_json))
    save_json(test_json, {"key": "val", "n": 42})
    loaded = load_json(test_json)
    assert loaded == {"key": "val", "n": 42}
    os.remove(test_json)

    passed("backend.utils.utils", "All path helpers + JSON roundtrip OK")
except Exception as e:
    failed("backend.utils.utils", str(e))


# ================================================================
# 2. BACKEND CORE MODULES
# ================================================================

section("2. BACKEND CORE MODULES")

# 2.1 Context Manager
try:
    from backend.core.context import ContextManager, get_context_manager
    ctx = ContextManager()
    assert ctx.current_language == 'en'
    assert ctx.wake_word == 'hey deskmate'
    assert ctx.dictation_mode == False

    fake_profile = {"username": "testuser", "language": "en", "wake_word": "hey deskmate"}
    ctx.set_user("testuser", fake_profile)
    assert ctx.current_user == "testuser"

    ctx.update_language('hi', 'Hindi')
    assert ctx.current_language == 'hi'

    ctx.set_active_app("chrome", "Google Chrome")
    assert ctx.active_app == "chrome"

    ctx.enter_dictation_mode()
    assert ctx.dictation_mode == True
    ctx.exit_dictation_mode()
    assert ctx.dictation_mode == False

    ctx.clear_user()
    assert ctx.current_user is None

    ctx2 = get_context_manager()
    ctx3 = get_context_manager()
    assert ctx2 is ctx3

    passed("backend.core.context", "ContextManager: all state transitions OK + singleton")
except Exception as e:
    failed("backend.core.context", str(e))

# 2.2 Memory Manager
try:
    from backend.core.memory import MemoryManager, get_memory_manager
    mem = MemoryManager()
    intents = mem.get_all_intents()
    assert isinstance(intents, dict) and len(intents) > 0
    assert "open_app" in intents and "close_app" in intents

    examples = mem.load_intent_examples()
    assert isinstance(examples, dict)

    stats = mem.get_memory_stats()
    assert isinstance(stats, dict)

    m2 = get_memory_manager()
    assert m2 is get_memory_manager()

    passed("backend.core.memory", f"MemoryManager: {len(intents)} intents + singleton OK")
except Exception as e:
    failed("backend.core.memory", str(e))

# 2.3 Registry
try:
    from backend.core.registry import CommandRegistry, get_registry, RegistryEntry
    reg = get_registry()
    entries = reg.get_all_entries()
    assert isinstance(entries, dict) and len(entries) > 0

    for intent in ["open_app", "close_app", "volume_up", "volume_down", "mute"]:
        entry = reg.get(intent)
        assert entry is not None, f"Intent '{intent}' not in registry"
        assert hasattr(entry, 'handler_function')
        assert hasattr(entry, 'needs_entity')

    assert reg.is_registered("open_app") == True
    assert reg.is_registered("__nonexistent__") == False

    assert reg is get_registry()

    passed("backend.core.registry", f"{len(entries)} intents registered + singleton OK")
except Exception as e:
    failed("backend.core.registry", str(e))

# 2.4 Command Executor
try:
    from backend.core.command_executor import CommandExecutor
    from backend.core.context import get_context_manager as gcm
    ex = CommandExecutor()
    ctx_obj = gcm()

    log1 = []
    def no_entity_handler():
        log1.append("ok")
        return "ok"

    class NoEntity:
        needs_entity = False

    ok, _ = ex.execute("t1", no_entity_handler, None, NoEntity(), ctx_obj)
    assert ok and "ok" in log1

    log2 = []
    def entity_handler(ent):
        log2.append(ent)
        return "ok"

    class WithEntity:
        needs_entity = True

    ok2, _ = ex.execute("t2", entity_handler, "chrome", WithEntity(), ctx_obj)
    assert ok2 and "chrome" in log2

    ok3, _ = ex.execute("t3", entity_handler, None, WithEntity(), ctx_obj)
    assert ok3 == False

    passed("backend.core.command_executor", "Execute, entity, missing-entity all correct")
except Exception as e:
    failed("backend.core.command_executor", str(e))

# 2.5 Command Handler
try:
    from backend.core.command_handler import CommandHandler, get_handler
    h = get_handler()
    assert hasattr(h, 'handle')
    assert h is get_handler()
    passed("backend.core.command_handler", "Singleton OK")
except Exception as e:
    failed("backend.core.command_handler", str(e))

# 2.6 Responder
try:
    from backend.core.responder import Responder, get_responder, RESPONSES
    r = get_responder()
    assert hasattr(r, 'speak')
    assert hasattr(r, 'speak_text')
    assert hasattr(r, 'get_response_text')
    assert hasattr(r, 'set_language')
    assert hasattr(r, 'is_speaking')
    assert hasattr(r, 'enable') and hasattr(r, 'disable')
    assert "en" in RESPONSES
    assert "opening_app" in RESPONSES["en"]
    assert "volume_up" in RESPONSES["en"]
    assert r is get_responder()
    passed("backend.core.responder", f"{len(RESPONSES['en'])} EN templates, singleton OK")
except Exception as e:
    failed("backend.core.responder", str(e))

# 2.7 Learner
try:
    from backend.core.learner import Learner, get_learner
    l = get_learner()
    assert hasattr(l, 'learn')
    assert l is get_learner()
    passed("backend.core.learner", "Singleton OK")
except Exception as e:
    failed("backend.core.learner", str(e))

# 2.8 Mapper
try:
    from backend.core.mapper import CommandMapper, get_mapper
    m = get_mapper()
    assert hasattr(m, 'map')
    assert hasattr(m, 'get_all_mapped_intents')
    assert hasattr(m, 'requires_confirmation')
    assert hasattr(m, 'get_response_key')
    assert hasattr(m, 'is_undoable')
    assert hasattr(m, 'clear_cache')
    assert m is get_mapper()
    passed("backend.core.mapper", "CommandMapper: 6 methods present, singleton OK")
except Exception as e:
    failed("backend.core.mapper", str(e))

# 2.9 Undo/Redo
try:
    from backend.core.undo_redo import UndoRedoManager, get_undo_redo_manager
    ur = get_undo_redo_manager()
    assert hasattr(ur, 'undo') and hasattr(ur, 'redo')
    assert ur is get_undo_redo_manager()
    passed("backend.core.undo_redo", "UndoRedoManager singleton OK")
except Exception as e:
    failed("backend.core.undo_redo", str(e))

# 2.10 Pipeline
try:
    from backend.core.pipeline import Pipeline
    p = Pipeline()
    assert hasattr(p, 'start') and hasattr(p, 'stop')
    assert p._running == False
    for cb in ['on_wake_word_detected', 'on_listening_start', 'on_listening_end',
               'on_transcription', 'on_intent_classified', 'on_command_executed',
               'on_error', 'on_status_change']:
        assert hasattr(p, cb), f"Missing: {cb}"
    passed("backend.core.pipeline", "Instantiated, all 8 callbacks present")
except Exception as e:
    failed("backend.core.pipeline", str(e))


# ================================================================
# 3. SECURITY MODULES
# ================================================================

section("3. SECURITY MODULES")

# 3.1 Password Auth
try:
    from backend.security.password_auth import PasswordAuth, get_password_auth
    pa = get_password_auth()
    for m in ['register_password', 'authenticate', 'is_password_registered',
              'hash_password', 'verify_password', 'check_password_strength']:
        assert hasattr(pa, m), f"Missing: {m}"
    strength = pa.check_password_strength("StrongPass123!")
    assert strength is not None
    assert pa is get_password_auth()
    passed("backend.security.password_auth", "6 methods present, strength check OK")
except Exception as e:
    failed("backend.security.password_auth", str(e))

# 3.2 Face Auth
try:
    from backend.security.face_auth import FaceAuth, get_face_auth
    fa = get_face_auth()
    for m in ['register', 'verify', 'is_registered', 'get_sample_count', 'delete_face_data']:
        assert hasattr(fa, m), f"Missing: {m}"
    assert fa is get_face_auth()
    passed("backend.security.face_auth", "5 methods present")
except Exception as e:
    failed("backend.security.face_auth", str(e))

# 3.3 Speech Auth
try:
    from backend.security.speech_auth import SpeechAuth, get_speech_auth
    sa = get_speech_auth()
    for m in ['register_speaker_profile', 'verify', 'register_voice_password',
              'login_with_voice_password', 'record_for_verification']:
        assert hasattr(sa, m), f"Missing: {m}"
    assert sa is get_speech_auth()
    passed("backend.security.speech_auth", "5 methods present")
except Exception as e:
    failed("backend.security.speech_auth", str(e))

# 3.4 Registration
try:
    from backend.security.registration import RegistrationManager, get_registration_manager
    rm = get_registration_manager()
    for m in ['register_basic_info', 'register_face', 'register_voice_password',
              'register_speaker_profile', 'complete_registration',
              'is_first_run', 'get_registration_status', 'get_all_users']:
        assert hasattr(rm, m), f"Missing: {m}"
    assert rm is get_registration_manager()
    passed("backend.security.registration", "8 methods present")
except Exception as e:
    failed("backend.security.registration", str(e))

# 3.5 Session Manager
try:
    from backend.security.session_manager import SessionManager, get_session_manager
    sm = get_session_manager()
    for m in ['create_session', 'get_current_session', 'get_current_user',
              'is_logged_in', 'is_admin', 'update_activity']:
        assert hasattr(sm, m), f"Missing: {m}"
    assert sm.is_logged_in() == False
    assert sm is get_session_manager()
    passed("backend.security.session_manager", "6 methods + initial state correct")
except Exception as e:
    failed("backend.security.session_manager", str(e))

# 3.6 Auth Orchestrator
try:
    from backend.security.auth_orchestrator import AuthOrchestrator, get_auth_orchestrator
    ao = get_auth_orchestrator()
    assert ao.password_auth is not None
    assert ao.face_auth is not None
    assert ao.registration is not None
    assert ao.session is not None
    assert hasattr(ao, 'speech_auth')  # lazy property
    assert ao is get_auth_orchestrator()
    passed("backend.security.auth_orchestrator", "All 5 sub-modules linked")
except Exception as e:
    failed("backend.security.auth_orchestrator", str(e))


# ================================================================
# 4. NLP MODULES
# ================================================================

section("4. NLP MODULES")

# 4.1 SBERT Engine
try:
    from NLP.nlp.sbert_engine import SBERTEngine, get_sbert_engine
    se = get_sbert_engine()
    assert hasattr(se, 'classify') and hasattr(se, 'build_embeddings')
    assert se._model_loaded == False
    assert se is get_sbert_engine()
    passed("NLP.nlp.sbert_engine", "Singleton OK, lazy-loaded")
except Exception as e:
    failed("NLP.nlp.sbert_engine", str(e))

# 4.2 LLM Fallback
try:
    from NLP.nlp.llm_fallback import LLMFallback, get_llm_fallback
    llm = get_llm_fallback()
    assert hasattr(llm, 'classify')
    assert llm is get_llm_fallback()
    passed("NLP.nlp.llm_fallback", "Singleton OK")
except Exception as e:
    failed("NLP.nlp.llm_fallback", str(e))

# 4.3 Intent Pipeline
try:
    from NLP.nlp.intent_pipeline import IntentPipeline, get_intent_pipeline
    ip = get_intent_pipeline()
    assert hasattr(ip, 'classify')
    assert ip._initialized == False
    assert ip is get_intent_pipeline()
    passed("NLP.nlp.intent_pipeline", "Singleton OK, lazy-loaded")
except Exception as e:
    failed("NLP.nlp.intent_pipeline", str(e))

# 4.4 Intent Examples JSON
try:
    from backend.utils.utils import get_intent_examples_path
    path = get_intent_examples_path()
    assert os.path.exists(path), f"Not found: {path}"
    with open(path, 'r') as f:
        data = json.load(f)
    assert isinstance(data, dict) and len(data) > 0
    required = ["open_app", "close_app", "volume_up", "volume_down"]
    missing = [i for i in required if i not in data]
    if missing:
        failed("NLP intents JSON", f"Missing: {missing}")
    else:
        passed("NLP intents JSON", f"{len(data)} intents found")
except Exception as e:
    failed("NLP intents JSON", str(e))

# 4.5 Intent Memory JSON
try:
    from backend.utils.utils import get_intent_memory_path
    path = get_intent_memory_path()
    if os.path.exists(path):
        with open(path, 'r') as f:
            data = json.load(f)
        passed("NLP intent memory JSON", f"{len(data)} learned entries")
    else:
        skipped("NLP intent memory JSON", "Not yet created — OK, generated on first learn")
except Exception as e:
    failed("NLP intent memory JSON", str(e))

# 4.6 Translator
try:
    from NLP.translation.translator import Translator, get_translator, translate
    t = get_translator()
    assert hasattr(t, 'detect_if_translation_needed')
    assert hasattr(t, 'get_supported_languages')
    assert hasattr(t, 'get_loaded_models')

    result = translate("open chrome", source_language="en")
    assert result == "open chrome", f"EN passthrough failed: got '{result}'"

    langs = t.get_supported_languages()
    assert 'hi' in langs or 'mr' in langs

    assert t is get_translator()
    passed("NLP.translation.translator", "EN passthrough OK, hi/mr supported")
except Exception as e:
    failed("NLP.translation.translator", str(e))


# ================================================================
# 5. SPEECH MODULES
# ================================================================

section("5. SPEECH MODULES")

# 5.1 ASR Loader
try:
    from NLP.speech.asr.asr_loader import ASRLoader, get_asr_loader
    al = get_asr_loader()
    assert hasattr(al, 'load_model') and hasattr(al, 'get_model')
    assert al._model_loaded == False
    assert "whisper" in al._model_dir.lower() or "models" in al._model_dir.lower()
    assert al is get_asr_loader()
    passed("NLP.speech.asr.asr_loader", "Singleton OK, lazy-loaded")
except Exception as e:
    failed("NLP.speech.asr.asr_loader", str(e))

# 5.2 ASR Model Files
try:
    from backend.utils.utils import get_whisper_model_dir
    d = get_whisper_model_dir()
    if os.path.exists(d) and os.listdir(d):
        passed("ASR model files", f"{len(os.listdir(d))} files in whisper dir")
    else:
        skipped("ASR model files", f"Place fine-tuned model at: NLP/models/whisper/")
except Exception as e:
    failed("ASR model files", str(e))

# 5.3 Speech Handler
try:
    from NLP.speech.asr.speech_handler import SpeechHandler, get_speech_handler
    sh = get_speech_handler()
    assert hasattr(sh, 'transcribe')
    assert sh is get_speech_handler()
    passed("NLP.speech.asr.speech_handler", "Singleton OK")
except Exception as e:
    failed("NLP.speech.asr.speech_handler", str(e))

# 5.4 Mic Stream
try:
    from NLP.speech.asr.mic_stream import MicStream, get_mic_stream
    ms = get_mic_stream()
    for m in ['record_command', 'record_dictation', 'record_fixed',
              'get_input_devices', 'get_default_device', 'test_microphone']:
        assert hasattr(ms, m), f"Missing: {m}"
    assert ms is get_mic_stream()
    passed("NLP.speech.asr.mic_stream", "6 methods present, singleton OK")
except Exception as e:
    failed("NLP.speech.asr.mic_stream", str(e))

# 5.5 Wake Word Detector
try:
    from NLP.speech.wakeword.wake_word_detector import WakeWordDetector, get_wake_word_detector
    ww = get_wake_word_detector()
    for m in ['listen', 'stop', 'test_wake_word', 'update_wake_word_settings']:
        assert hasattr(ww, m), f"Missing: {m}"
    assert ww is get_wake_word_detector()
    passed("NLP.speech.wakeword.wake_word_detector", "4 methods present, singleton OK")
except Exception as e:
    failed("NLP.speech.wakeword.wake_word_detector", str(e))

# 5.6 Noise Reduction
try:
    import numpy as np
    from NLP.speech.preprocessing.noise_reduction import NoiseReducer, get_noise_reducer, reduce_noise
    nr = get_noise_reducer()
    assert hasattr(nr, 'reduce_noise')
    assert hasattr(nr, 'reduce_noise_advanced')
    assert hasattr(nr, 'smart_reduce')
    assert hasattr(nr, 'estimate_noise_level')
    dummy = np.zeros(16000, dtype=np.float32)
    result = nr.reduce_noise(dummy)
    assert result is not None and len(result) > 0
    # Also test module-level function
    result2 = reduce_noise(dummy)
    assert result2 is not None
    passed("NLP.speech.preprocessing.noise_reduction", "reduce_noise() + smart_reduce() + module fn OK")
except Exception as e:
    failed("NLP.speech.preprocessing.noise_reduction", str(e))

# 5.7 Normalize Audio
try:
    import numpy as np
    from NLP.speech.preprocessing.normalize_audio import AudioNormalizer, get_normalizer, normalize_audio
    an = get_normalizer()
    assert hasattr(an, 'normalize')
    dummy = np.array([0.1, -0.5, 0.3, 0.8, -0.2], dtype=np.float32)
    assert an.normalize(dummy) is not None
    assert normalize_audio(dummy) is not None
    passed("NLP.speech.preprocessing.normalize_audio", "normalize() + normalize_audio() OK")
except Exception as e:
    failed("NLP.speech.preprocessing.normalize_audio", str(e))

# 5.8 Silence Trim
try:
    import numpy as np
    from NLP.speech.preprocessing.silence_trim import SilenceTrimmer, get_silence_trimmer, trim_silence
    st = get_silence_trimmer()
    assert hasattr(st, 'trim_silence')
    assert hasattr(st, 'remove_silence_gaps')
    assert hasattr(st, 'is_silent')
    assert hasattr(st, 'has_speech')
    assert hasattr(st, 'full_process')
    dummy = np.zeros(16000, dtype=np.float32)
    result = st.trim_silence(dummy)
    assert result is not None
    # Also test module-level function
    result2 = trim_silence(dummy)
    assert result2 is not None
    passed("NLP.speech.preprocessing.silence_trim", "trim_silence() + module fn OK")
except Exception as e:
    failed("NLP.speech.preprocessing.silence_trim", str(e))


# ================================================================
# 6. AUTOMATION MODULES
# ================================================================

section("6. AUTOMATION MODULES  (function-based — import + function presence)")

automation_checks = [
    ("backend.automation.app_launcher",
     ["open_app", "close_app", "switch_to_app", "is_app_open", "get_open_apps"]),
    ("backend.automation.media_controls",
     ["play_pause", "play", "pause", "next_track", "previous_track", "stop",
      "spotify_play_pause", "vlc_play_pause", "youtube_play_pause"]),
    ("backend.automation.system_controls",
     ["shutdown", "restart", "lock_screen", "sleep"]),
    ("backend.automation.ui_clicking",
     ["click_element", "left_click", "right_click", "double_click",
      "scroll_up", "scroll_down", "move_mouse_to", "drag_to"]),
    ("backend.automation.ui_typing",
     ["type_text", "copy_text", "paste_text", "select_all",
      "undo_typing", "redo_typing", "save_file", "find_text"]),
    ("backend.automation.web_interaction",
     ["search", "search_youtube", "new_tab", "close_tab",
      "go_back", "go_forward", "refresh_page", "go_to_url"]),
    ("backend.automation.app_workflows",
     ["minimize_window", "maximize_window", "restore_window", "close_window",
      "switch_window", "take_screenshot", "snap_window_left", "snap_window_right"]),
]

for module_path, expected_fns in automation_checks:
    try:
        import importlib
        mod = importlib.import_module(module_path)
        missing = [fn for fn in expected_fns if not hasattr(mod, fn)]
        if missing:
            failed(module_path, f"Missing functions: {missing}")
        else:
            passed(module_path, f"{len(expected_fns)} functions present")
    except Exception as e:
        failed(module_path, str(e))


# ================================================================
# 7. UI MODULES  (import only)
# ================================================================

section("7. UI MODULES  (import-only — no display needed)")

ui_modules = [
    "ui.controller",
    "ui.tray_icon",
    "ui.animations.status_indicator",
    "ui.animations.waveform",
    "ui.views.dashboard_window",
    "ui.views.login_window",
    "ui.views.main_window",
    "ui.views.register_window",
    "ui.views.settings_window",
]

for module_path in ui_modules:
    try:
        import importlib
        importlib.import_module(module_path)
        passed(module_path, "Import OK")
    except ImportError as e:
        err = str(e)
        if "PyQt6" in err or "Qt" in err:
            skipped(module_path, "PyQt6 not installed in test env (run on Windows with PyQt6)")
        else:
            failed(module_path, err)
    except Exception as e:
        failed(module_path, str(e))


# ================================================================
# 8. INTEGRATION CHECKS
# ================================================================

section("8. INTEGRATION CHECKS  (cross-module wiring)")

# 8.1 Registry <-> Memory coverage
try:
    from backend.core.registry import get_registry
    from backend.core.memory import get_memory_manager
    reg = get_registry()
    mem = get_memory_manager()
    all_intents = set(mem.get_all_intents().keys())
    reg_intents = set(reg.get_all_entries().keys())
    missing_examples = reg_intents - all_intents
    extra_examples   = all_intents - reg_intents

    if not missing_examples:
        passed("Registry <-> Memory", f"All {len(reg_intents)} registry intents have training examples")
    else:
        failed("Registry <-> Memory",
               f"{len(missing_examples)} intents in registry but no examples: {missing_examples}")
    if extra_examples:
        print(f"    {YELLOW}[NOTE]{RESET} {len(extra_examples)} intents have examples but no registry entry: {extra_examples}")
except Exception as e:
    failed("Registry <-> Memory", str(e))

# 8.2 Context <-> Pipeline singleton
try:
    from backend.core.pipeline import Pipeline
    from backend.core.context import get_context_manager
    p = Pipeline()
    assert p.context is get_context_manager()
    passed("Context <-> Pipeline", "Pipeline uses shared context singleton")
except Exception as e:
    failed("Context <-> Pipeline", str(e))

# 8.3 Translator EN passthrough
try:
    from NLP.translation.translator import translate
    for text in ["close chrome", "open notepad", "volume up"]:
        result = translate(text, source_language="en")
        assert result == text, f"Broken for '{text}': got '{result}'"
    passed("Translator EN passthrough", "3 EN phrases pass through unchanged")
except Exception as e:
    failed("Translator EN passthrough", str(e))

# 8.4 Data directory structure
try:
    from backend.utils.utils import (
        get_data_dir, get_users_dir, get_intents_dir,
        get_intent_examples_path, ensure_dir
    )
    for d in [get_data_dir(), get_users_dir(), get_intents_dir()]:
        ensure_dir(d)
        assert os.path.exists(d)
    assert os.path.exists(get_intent_examples_path())
    passed("Data directory structure", "All critical dirs + intent_examples.json present")
except Exception as e:
    failed("Data directory structure", str(e))

# 8.5 Auth chain completeness
try:
    from backend.security.auth_orchestrator import get_auth_orchestrator
    ao = get_auth_orchestrator()
    assert ao.password_auth is not None
    assert ao.face_auth is not None
    assert ao.registration is not None
    assert ao.session is not None
    passed("Auth chain", "PasswordAuth, FaceAuth, Registration, Session all linked")
except Exception as e:
    failed("Auth chain", str(e))


# ================================================================
# SUMMARY
# ================================================================

section("SUMMARY")

total  = len(results)
passes = sum(1 for r in results if r[0] == "PASS")
fails  = sum(1 for r in results if r[0] == "FAIL")
skips  = sum(1 for r in results if r[0] == "SKIP")

print(f"\n  Total:   {total}")
print(f"  {GREEN}{BOLD}Passed:  {passes}{RESET}")
print(f"  {RED}{BOLD}Failed:  {fails}{RESET}")
print(f"  {YELLOW}{BOLD}Skipped: {skips}{RESET}")

if fails > 0:
    print(f"\n{RED}{BOLD}  -- Failed Tests --{RESET}")
    for status, name, detail in results:
        if status == "FAIL":
            print(f"  {RED}x {name}{RESET}")
            if detail:
                print(f"      {detail}")

print(f"\n{CYAN}{'─'*60}{RESET}\n")
sys.exit(0 if fails == 0 else 1)
