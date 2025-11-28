import os
import logging
from logging.handlers import RotatingFileHandler

def get_env_var(name, default=None, required=False):
    value = os.getenv(name, default)
    if required and (value is None or value == default):
        raise EnvironmentError(
            f"Missing required environment variable: {name}. "
            f"Set it in your host/platform’s environment settings."
        )
    return value

# --- ENVIRONMENT VARIABLES ---
TELEGRAM_TOKEN = get_env_var("TELEGRAM_TOKEN", "YOUR_TELEGRAM_TOKEN", required=True)
BOT_OWNER_ID = get_env_var("BOT_OWNER_ID", None, required=True) # Must be set
PUBLIC_URL = get_env_var("PUBLIC_URL", "https://your-deployment-name.koyeb.app") # Webhook etc

# --- CONSTANTS ---
LOG_FILE = "bot_activity.log"
LOG_MAX_BYTES = 1024 * 1024  # 1 MB
LOG_BACKUP_COUNT = 3

FAILED_TASKS_FILE = "failed_tasks.json"
BOT_CONFIG_FILE = "bot_config.json"

MAX_CAPTION_LENGTH = 4000
MAX_FILE_SIZE_MB = 20

# Logging setup
LOGGER = logging.getLogger("ForwardCaptionRemoverBot")
LOGGER.setLevel(logging.INFO)
formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")
handler = RotatingFileHandler(LOG_FILE, maxBytes=LOG_MAX_BYTES, backupCount=LOG_BACKUP_COUNT)
handler.setFormatter(formatter)
LOGGER.addHandler(handler)

def validate_config():
    try:
        assert TELEGRAM_TOKEN != "YOUR_TELEGRAM_TOKEN" and TELEGRAM_TOKEN, "Invalid TELEGRAM_TOKEN!"
        assert BOT_OWNER_ID and BOT_OWNER_ID != "12345678", "Invalid BOT_OWNER_ID!"
    except AssertionError as e:
        LOGGER.critical(str(e))
        return False
    return True
