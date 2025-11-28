# Configuration settings, environment variables, and constants.

import os
import logging
from logging.handlers import RotatingFileHandler

# --- ENVIRONMENT VARIABLES ---
# These must be set in your Koyeb environment settings.
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN")
BOT_OWNER_ID = os.getenv("BOT_OWNER_ID", "12345678") # Replace with your actual Telegram User ID (as a string)
PUBLIC_URL = os.getenv("PUBLIC_URL", "https://your-deployment-name.koyeb.app") # The public URL Koyeb assigns to your app

# --- CONSTANTS ---
LOG_FILE = "bot_activity.log"
LOG_MAX_BYTES = 1024 * 1024  # 1 MB max log size
LOG_BACKUP_COUNT = 3

# File paths for persistent storage on disk
FAILED_TASKS_FILE = "failed_tasks.json"
BOT_CONFIG_FILE = "bot_config.json"

# Telegram API Limits
MAX_CAPTION_LENGTH = 4000 # Safe limit for text splitting
MAX_FILE_SIZE_MB = 20 # Maximum file size the bot will attempt to process (Resource protection)

# --- LOGGING SETUP ---
def setup_logging():
    """Configures the logger to write to console and a rotating file."""
    logger = logging.getLogger('telegram_bot')
    logger.setLevel(logging.INFO)

    # Console Handler (for standard output/Koyeb logs)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Rotating File Handler (for /log command)
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=LOG_MAX_BYTES,
        backupCount=LOG_BACKUP_COUNT,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger

LOGGER = setup_logging()

# --- INITIAL RUNTIME CHECKS ---
def validate_config():
    """Checks for essential environment variables."""
    if TELEGRAM_TOKEN == "YOUR_TELEGRAM_TOKEN" or BOT_OWNER_ID == "12345678":
        LOGGER.error("CRITICAL: TELEGRAM_TOKEN or BOT_OWNER_ID is not set correctly. Bot will not function.")
        return False
    if PUBLIC_URL == "https://your-deployment-name.koyeb.app":
        LOGGER.warning("WARNING: PUBLIC_URL is using the default placeholder. Wake-up link will be incorrect.")
    return True

if not validate_config():
    import sys
    sys.exit(1) # Exit immediately if critical config is missing
