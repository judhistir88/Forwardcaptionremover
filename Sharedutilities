# Utility functions for file persistence, rate limiting, and content cleanup.

import json
import time
import os
import re
from datetime import datetime
from config import BOT_CONFIG_FILE, FAILED_TASKS_FILE, LOGGER, MAX_CAPTION_LENGTH, PUBLIC_URL

# --- RATE LIMITING ---
LAST_API_CALL_TIME = 0.0
# The time delay required between API calls to avoid Telegram blocking.
# Set a lower limit for internal commands and a higher limit for external tasks.
TELEGRAM_API_DELAY_SECONDS = 0.3

def enforce_api_rate_limit(internal=False):
    """Enforces a delay between API calls."""
    global LAST_API_CALL_TIME
    delay = 0.1 if internal else TELEGRAM_API_DELAY_SECONDS
    elapsed = time.time() - LAST_API_CALL_TIME
    if elapsed < delay:
        sleep_time = delay - elapsed
        time.sleep(sleep_time)
    LAST_API_CALL_TIME = time.time()

# --- JSON PERSISTENCE (Configuration) ---

DEFAULT_CONFIG = {
    "STICKER_BLOCK_ENABLED": True,
    "PHOTO_VIDEO_ONLY_ENABLED": True,
    "CLEANUP_STRINGS": [
        "Shared via Telegram",
        "t.me/",
        "forwarded from"
    ],
    "LAST_LINK_MESSAGE_ID": None  # Stores the message_id of the last sent wake-up link
}

def load_config():
    """Loads bot configuration from the persistent JSON file."""
    try:
        with open(BOT_CONFIG_FILE, 'r') as f:
            config = json.load(f)
            # Ensure the structure matches default in case keys are missing
            return {**DEFAULT_CONFIG, **config}
    except (FileNotFoundError, json.JSONDecodeError):
        # Create file if it doesn't exist or is corrupt
        save_config(DEFAULT_CONFIG)
        return DEFAULT_CONFIG

def save_config(config):
    """Saves bot configuration to the persistent JSON file."""
    try:
        with open(BOT_CONFIG_FILE, 'w') as f:
            json.dump(config, f, indent=4)
    except IOError as e:
        LOGGER.error(f"Failed to save configuration: {e}")

def get_config_value(key):
    """Gets a specific value from the current configuration."""
    return load_config().get(key, DEFAULT_CONFIG.get(key))

def set_config_value(key, value):
    """Sets and saves a specific configuration value."""
    config = load_config()
    config[key] = value
    save_config(config)

# --- JSON PERSISTENCE (Failed Tasks) ---

def load_failed_tasks():
    """Loads failed tasks from the persistent JSON file."""
    try:
        with open(FAILED_TASKS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_failed_tasks(tasks):
    """Saves failed tasks to the persistent JSON file."""
    try:
        with open(FAILED_TASKS_FILE, 'w') as f:
            json.dump(tasks, f, indent=4)
    except IOError as e:
        LOGGER.error(f"Failed to save failed tasks: {e}")

# --- TELEGRAM LINK GENERATION ---

def generate_telegram_link(chat_id, message_id, bot_username=""):
    """
    Generates a clickable link to a specific message.
    Assumes private chat with C_ID format (e.g., -1001234567890).
    """
    # Strips the leading negative sign from private chat IDs for the link format.
    clean_chat_id = str(chat_id).replace("-100", "")
    return f"https://t.me/c/{clean_chat_id}/{message_id}"

# --- CONTENT CLEANUP ---

def is_full_hyperlink(text):
    """Checks if the entire text is a markdown hyperlink structure."""
    return bool(re.fullmatch(r'\[.+\]\(.+\)', text.strip()))

def clean_message_text(text):
    """Applies complex cleanup rules to the message text."""
    if not text:
        return ""

    original_text = text

    # --- 1. Full Hyperlink Conversion (Protection against unwanted command stripping) ---
    if is_full_hyperlink(original_text):
        # Extract the display text from the markdown link: [Display Text](URL)
        match = re.match(r'\[(.+?)\]\(.+\)', original_text.strip())
        if match:
            display_text = match.group(1).strip()
            # Protect if the display text contains a bot command
            if display_text.startswith('/'):
                pass  # Keep the link structure to protect the command
            else:
                original_text = display_text # Convert link to plain text

    # --- 2. Global Username and HTML Tag Stripping ---
    # Removes all @usernames
    cleaned_text = re.sub(r'@\w+', '', original_text, flags=re.IGNORECASE).strip()
    # Removes simple HTML tags that might survive Telegram formatting
    cleaned_text = re.sub(r'<[^>]+>', '', cleaned_text).strip()

    # --- 3. Custom Cleanup String Removal ---
    cleanup_strings = get_config_value("CLEANUP_STRINGS")
    for phrase in cleanup_strings:
        # Use re.IGNORECASE for more robust removal
        cleaned_text = re.sub(re.escape(phrase), '', cleaned_text, flags=re.IGNORECASE).strip()

    # Removes excess whitespace caused by removals
    cleaned_text = re.sub(r'\s+', ' ', cleaned_text).strip()

    return cleaned_text

# --- MESSAGE SPLITTING ---

def split_long_message(text):
    """Splits text into chunks respecting Telegram's limit, adding numbering."""
    chunks = []
    if not text:
        return [""]

    if len(text) <= MAX_CAPTION_LENGTH:
        return [text]

    start = 0
    while start < len(text):
        end = min(start + MAX_CAPTION_LENGTH, len(text))

        if end < len(text):
            # Try to find a natural breaking point (newline or sentence end)
            best_break = end
            for char in '\n.!?':
                # Look back from the max length to avoid splitting words
                search_end = min(end, start + MAX_CAPTION_LENGTH)
                last_occurrence = text.rfind(char, start, search_end)
                if last_occurrence > start + MAX_CAPTION_LENGTH * 0.8: # Ensure break is close to the max limit
                    best_break = last_occurrence + (1 if char == '\n' else 0)
                    break
            
            end = best_break
        
        chunks.append(text[start:end].strip())
        start = end

    # Apply part numbering
    final_chunks = []
    total_parts = len(chunks)
    for i, chunk in enumerate(chunks):
        part_tag = f"\n\n--- (Part {i + 1} of {total_parts}) ---"
        if len(chunk) + len(part_tag) <= MAX_CAPTION_LENGTH:
            final_chunks.append(chunk + part_tag)
        else:
            # Should rarely happen, but handles case where chunk is exactly MAX_CAPTION_LENGTH
            final_chunks.append(chunk)

    return final_chunks


