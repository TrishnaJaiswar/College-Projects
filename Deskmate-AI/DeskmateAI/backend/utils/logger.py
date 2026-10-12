# DeskmateAI/backend/utils/logger.py

import logging
import os
from datetime import datetime

# ============================================================
# LOGGER SETUP FOR DESKMATEAI
# Handles all logging across the entire system
# Persists logs to file even after system closes
# ============================================================

# Log file location — persists across sessions
LOG_DIR = os.path.join(os.path.dirname(__file__), '..', 'data', 'logs')
LOG_FILE = os.path.join(LOG_DIR, 'deskmateai.log')

def setup_logger():
    # print("[LOGGER] Setting up logger...")

    # Create logs directory if not exists
    os.makedirs(LOG_DIR, exist_ok=True)

    # Create logger
    logger = logging.getLogger('DeskmateAI')
    logger.setLevel(logging.DEBUG)

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # File handler — persists logs to disk
    file_handler = logging.FileHandler(LOG_FILE, encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)

    # Console handler — shows logs in terminal
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)

    # Format
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] [%(module)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    # print("[LOGGER] Logger setup complete")
    return logger

# Global logger instance
logger = setup_logger()

def log_info(message):
    # print(f"[LOG INFO] {message}")
    logger.info(message)

def log_debug(message):
    # print(f"[LOG DEBUG] {message}")
    logger.debug(message)

def log_warning(message):
    # print(f"[LOG WARNING] {message}")
    logger.warning(message)

def log_error(message):
    # print(f"[LOG ERROR] {message}")
    logger.error(message)

def log_critical(message):
    # print(f"[LOG CRITICAL] {message}")
    logger.critical(message)

def log_action(user, intent, command, result):
    # print(f"[LOG ACTION] User: {user} | Intent: {intent} | Command: {command} | Result: {result}")
    logger.info(f"ACTION | User: {user} | Intent: {intent} | Command: {command} | Result: {result}")

def log_auth(user, method, success):
    # print(f"[LOG AUTH] User: {user} | Method: {method} | Success: {success}")
    logger.info(f"AUTH | User: {user} | Method: {method} | Success: {success}")

def log_intent(command, intent, score, source):
    # print(f"[LOG INTENT] Command: {command} | Intent: {intent} | Score: {score} | Source: {source}")
    logger.info(f"INTENT | Command: {command} | Intent: {intent} | Score: {score:.2f} | Source: {source}")

def log_wake_word(detected_text, wake_word):
    # print(f"[LOG WAKE] Detected: {detected_text} | Wake Word: {wake_word}")
    logger.info(f"WAKE | Detected: {detected_text} | Wake Word: {wake_word}")

def log_error_trace(message, exception):
    # print(f"[LOG ERROR TRACE] {message} | Exception: {str(exception)}")
    logger.error(f"{message} | Exception: {str(exception)}", exc_info=True)

def get_log_file_path():
    return LOG_FILE

def clear_logs():
    # print("[LOGGER] Clearing logs...")
    open(LOG_FILE, 'w').close()
    logger.info("Logs cleared")