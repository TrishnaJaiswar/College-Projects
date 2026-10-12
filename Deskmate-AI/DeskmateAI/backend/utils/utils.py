# DeskmateAI/backend/utils/utils.py

import os
import json
import numpy as np
from datetime import datetime
import hashlib
import shutil

# ============================================================
# UTILITY FUNCTIONS FOR DESKMATEAI
# Helper functions used across entire system
# ============================================================

# ── Path Helpers ────────────────────────────────────────────

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_base_dir():
    # print(f"[UTILS] Base dir: {BASE_DIR}")
    return BASE_DIR

def get_backend_dir():
    return os.path.join(BASE_DIR, 'backend')

def get_data_dir():
    return os.path.join(BASE_DIR, 'backend', 'data')

def get_users_dir():
    return os.path.join(BASE_DIR, 'backend', 'data', 'users')

def get_user_dir(username):
    return os.path.join(get_users_dir(), username)

def get_user_speaker_dir(username):
    return os.path.join(get_user_dir(username), 'speaker_profile')

def get_user_face_dir(username):
    return os.path.join(get_user_dir(username), 'face_profile')

def get_user_voice_pass_dir(username):
    return os.path.join(get_user_dir(username), 'voice_password')

def get_nlp_dir():
    return os.path.join(BASE_DIR, 'NLP')

def get_models_dir():
    return os.path.join(BASE_DIR, 'NLP', 'models')

def get_whisper_model_dir():
    return os.path.join(BASE_DIR, 'NLP', 'models', 'whisper')

def get_translation_model_dir():
    return os.path.join(BASE_DIR, 'NLP', 'models', 'translation')

def get_wakeword_model_dir():
    return os.path.join(BASE_DIR, 'NLP', 'models', 'wakeword')

def get_intents_dir():
    return os.path.join(BASE_DIR, 'NLP', 'nlp', 'intents')

def get_intent_examples_path():
    return os.path.join(get_intents_dir(), 'intent_examples.json')

def get_intent_memory_path():
    return os.path.join(get_intents_dir(), 'intent_memory.json')

def get_logs_dir():
    return os.path.join(BASE_DIR, 'backend', 'data', 'logs')

# ── JSON Helpers ─────────────────────────────────────────────

def load_json(filepath):
    # print(f"[UTILS] Loading JSON: {filepath}")
    try:
        if not os.path.exists(filepath):
            # print(f"[UTILS] File not found, returning empty dict: {filepath}")
            return {}
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except Exception as e:
        # print(f"[UTILS] Error loading JSON {filepath}: {e}")
        return {}

def save_json(filepath, data):
    # print(f"[UTILS] Saving JSON: {filepath}")
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        # print(f"[UTILS] JSON saved successfully: {filepath}")
        return True
    except Exception as e:
        # print(f"[UTILS] Error saving JSON {filepath}: {e}")
        return False

def update_json(filepath, key, value):
    # print(f"[UTILS] Updating JSON key '{key}' in {filepath}")
    data = load_json(filepath)
    data[key] = value
    return save_json(filepath, data)

# ── Numpy Helpers ─────────────────────────────────────────────

def save_numpy(filepath, array):
    # print(f"[UTILS] Saving numpy array: {filepath}")
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        np.save(filepath, array)
        # print(f"[UTILS] Numpy saved: {filepath}")
        return True
    except Exception as e:
        # print(f"[UTILS] Error saving numpy {filepath}: {e}")
        return False

def load_numpy(filepath):
    # print(f"[UTILS] Loading numpy array: {filepath}")
    try:
        if not os.path.exists(filepath):
            # print(f"[UTILS] Numpy file not found: {filepath}")
            return None
        return np.load(filepath, allow_pickle=True)
    except Exception as e:
        # print(f"[UTILS] Error loading numpy {filepath}: {e}")
        return None

# ── Directory Helpers ─────────────────────────────────────────

def ensure_dir(path):
    # print(f"[UTILS] Ensuring directory: {path}")
    os.makedirs(path, exist_ok=True)

def create_user_dirs(username):
    # print(f"[UTILS] Creating directories for user: {username}")
    dirs = [
        get_user_dir(username),
        get_user_speaker_dir(username),
        get_user_face_dir(username),
        get_user_voice_pass_dir(username)
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)
        # print(f"[UTILS] Created: {d}")
    return True

def delete_user_dirs(username):
    # print(f"[UTILS] Deleting directories for user: {username}")
    user_dir = get_user_dir(username)
    if os.path.exists(user_dir):
        shutil.rmtree(user_dir)
        # print(f"[UTILS] Deleted user dir: {user_dir}")
        return True
    return False

def list_users():
    # print("[UTILS] Listing all users...")
    users_dir = get_users_dir()
    if not os.path.exists(users_dir):
        return []
    users = [d for d in os.listdir(users_dir)
             if os.path.isdir(os.path.join(users_dir, d))]
    # print(f"[UTILS] Found users: {users}")
    return users

def user_exists(username):
    return os.path.exists(get_user_dir(username))

# ── Profile Helpers ───────────────────────────────────────────

def get_profile_path(username):
    return os.path.join(get_user_dir(username), 'profile.json')

def load_profile(username):
    # print(f"[UTILS] Loading profile for: {username}")
    return load_json(get_profile_path(username))

def save_profile(username, profile_data):
    # print(f"[UTILS] Saving profile for: {username}")
    return save_json(get_profile_path(username), profile_data)

def update_profile(username, key, value):
    # print(f"[UTILS] Updating profile key '{key}' for: {username}")
    profile = load_profile(username)
    profile[key] = value
    return save_profile(username, profile)

def get_admin_user():
    # print("[UTILS] Getting admin user...")
    users = list_users()
    for username in users:
        profile = load_profile(username)
        if profile.get('is_admin', False):
            # print(f"[UTILS] Admin found: {username}")
            return username
    return None

def is_first_run():
    users = list_users()
    result = len(users) == 0
    # print(f"[UTILS] Is first run: {result}")
    return result

# ── Date/Time Helpers ─────────────────────────────────────────

def get_timestamp():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def get_date():
    return datetime.now().strftime('%Y-%m-%d')

# ── String Helpers ─────────────────────────────────────────────

def normalize_text(text):
    # print(f"[UTILS] Normalizing text: {text}")
    if not text:
        return ""
    return text.lower().strip()

def extract_app_name(command):
    # print(f"[UTILS] Extracting app name from: {command}")
    # Remove common words to extract app name
    remove_words = [
        'open', 'launch', 'start', 'run', 'close',
        'exit', 'shut', 'down', 'the', 'app', 'application',
        'please', 'can', 'you', 'me', 'a', 'an'
    ]
    words = command.lower().split()
    app_words = [w for w in words if w not in remove_words]
    result = ' '.join(app_words).strip()
    # print(f"[UTILS] Extracted app name: {result}")
    return result

def extract_search_query(command):
    # print(f"[UTILS] Extracting search query from: {command}")
    remove_words = [
        'search', 'for', 'google', 'look', 'up',
        'find', 'information', 'about', 'on', 'the'
    ]
    words = command.lower().split()
    query_words = [w for w in words if w not in remove_words]
    result = ' '.join(query_words).strip()
    # print(f"[UTILS] Extracted search query: {result}")
    return result

def extract_volume_level(command):
    # print(f"[UTILS] Extracting volume level from: {command}")
    words = command.lower().split()
    for word in words:
        if word.isdigit():
            level = int(word)
            if 0 <= level <= 100:
                # print(f"[UTILS] Extracted volume level: {level}")
                return level
    return None

def extract_brightness_level(command):
    # print(f"[UTILS] Extracting brightness level from: {command}")
    words = command.lower().split()
    for word in words:
        if word.isdigit():
            level = int(word)
            if 0 <= level <= 100:
                # print(f"[UTILS] Extracted brightness level: {level}")
                return level
    return None

def process_punctuation(text):
    # print(f"[UTILS] Processing punctuation in: {text}")
    replacements = {
        ' comma ': ', ',
        ' full stop ': '. ',
        ' period ': '. ',
        ' question mark ': '? ',
        ' exclamation mark ': '! ',
        ' exclamation point ': '! ',
        ' new line ': '\n',
        ' newline ': '\n',
        ' colon ': ': ',
        ' semicolon ': '; ',
        ' hyphen ': '-',
        ' dash ': '-',
        ' open bracket ': '(',
        ' close bracket ': ')',
        ' open parenthesis ': '(',
        ' close parenthesis ': ')',
        # Hindi punctuation words
        ' अल्पविराम ': ', ',
        ' पूर्णविराम ': '। ',
        ' प्रश्नचिह्न ': '? ',
        # Marathi punctuation words
        ' स्वल्पविराम ': ', ',
        ' पूर्णविराम ': '। ',
    }
    result = ' ' + text + ' '
    for word, symbol in replacements.items():
        result = result.replace(word, symbol)
    # print(f"[UTILS] Processed text: {result.strip()}")
    return result.strip()

# ── Validation Helpers ────────────────────────────────────────

def validate_username(username):
    # print(f"[UTILS] Validating username: {username}")
    if not username:
        return False, "Username cannot be empty"
    if len(username) < 3:
        return False, "Username must be at least 3 characters"
    if len(username) > 20:
        return False, "Username must be less than 20 characters"
    if not username.replace('_', '').replace('-', '').isalnum():
        return False, "Username can only contain letters, numbers, _ and -"
    return True, "Valid"

def validate_password(password):
    # print(f"[UTILS] Validating password")
    if not password:
        return False, "Password cannot be empty"
    if len(password) < 6:
        return False, "Password must be at least 6 characters"
    return True, "Valid"

def validate_wake_word(wake_word):
    # print(f"[UTILS] Validating wake word: {wake_word}")
    if not wake_word:
        return False, "Wake word cannot be empty"
    if len(wake_word.split()) < 1:
        return False, "Wake word must have at least one word"
    return True, "Valid"

# ── Language Helpers ──────────────────────────────────────────

SUPPORTED_LANGUAGES = {
    'en': 'English',
    'hi': 'Hindi',
    'mr': 'Marathi'
}

def get_language_name(code):
    return SUPPORTED_LANGUAGES.get(code, 'English')

def get_language_code(name):
    for code, lang_name in SUPPORTED_LANGUAGES.items():
        if lang_name.lower() == name.lower():
            return code
    return 'en'

def is_supported_language(code):
    return code in SUPPORTED_LANGUAGES