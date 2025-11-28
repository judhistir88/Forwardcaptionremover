# Simulates the Telegram Bot API methods, handling persistence and rate limits.

import time
import random
from datetime import datetime
from config import LOGGER, BOT_OWNER_ID, TELEGRAM_TOKEN, PUBLIC_URL, MAX_FILE_SIZE_MB
from utils import (
    enforce_api_rate_limit, load_failed_tasks, save_failed_tasks,
    clean_message_text, split_long_message, get_config_value, set_config_value,
    generate_telegram_link
)

# --- MOCK STATE ---
# Mock Message ID counter to simulate Telegram's sequential message IDs
MOCK_MESSAGE_ID_COUNTER = 1000

def get_next_mock_message_id():
    """Increments and returns the next mock message ID."""
    global MOCK_MESSAGE_ID_COUNTER
    MOCK_MESSAGE_ID_COUNTER += 1
    return MOCK_MESSAGE_ID_COUNTER

# --- CORE API MOCK FUNCTIONS ---

def api_send_message(chat_id, text):
    """Simulates sending a text message."""
    enforce_api_rate_limit()
    
    # Simulate message splitting for long responses
    chunks = split_long_message(text)
    
    message_ids = []
    for chunk in chunks:
        # Simulate API call for each chunk
        msg_id = get_next_mock_message_id()
        LOGGER.info(f"API MOCK: Sending message (ID:{msg_id}) to chat {chat_id}. Content: '{chunk[:50]}...'")
        message_ids.append(msg_id)
        # In a real app, this returns the message object; here we just return the IDs.

    # Return the message ID of the last chunk sent
    return message_ids[-1] if message_ids else None

def api_delete_message(chat_id, message_id):
    """Simulates deleting a message."""
    enforce_api_rate_limit(internal=True)
    LOGGER.info(f"API MOCK: DELETING message (ID:{message_id}) from chat {chat_id}.")
    return True

def api_send_document(chat_id, file_content, filename):
    """Simulates sending a document (used for log file)."""
    enforce_api_rate_limit()
    LOGGER.info(f"API MOCK: Sending document '{filename}' to chat {chat_id}.")
    return True

def api_leave_chat(chat_id):
    """Simulates the bot leaving the chat (used for unauthorized users)."""
    enforce_api_rate_limit(internal=True)
    LOGGER.warning(f"API MOCK: Bot leaving unauthorized chat {chat_id}.")
    return True

# --- INLINE KEYBOARD MOCK FUNCTIONS ---

def api_send_inline_keyboard(chat_id, text, reply_markup):
    """Simulates sending a message with an inline keyboard."""
    enforce_api_rate_limit()
    msg_id = get_next_mock_message_id()
    LOGGER.info(f"API MOCK: Sending inline keyboard (ID:{msg_id}) to chat {chat_id}. Buttons: {len(reply_markup['inline_keyboard'][0])}")
    # In a real library, this returns the message object, including the message_id
    return msg_id

def api_edit_message_reply_markup(chat_id, message_id, reply_markup):
    """Simulates editing only the buttons of a previously sent message."""
    enforce_api_rate_limit(internal=True)
    LOGGER.info(f"API MOCK: Editing reply markup for message {message_id} in chat {chat_id}.")
    return True

# --- WAKE-UP LINK LOGIC ---

def send_wake_up_link(chat_id):
    """
    Sends the persistent wake-up link, deleting the previous one to keep chat clutter-free.
    Returns the message ID of the new link.
    """
    last_link_id = get_config_value("LAST_LINK_MESSAGE_ID")
    
    # 1. DELETE previous link if it exists
    if last_link_id:
        api_delete_message(chat_id, last_link_id)

    # 2. Prepare the new link and button
    link_text = (
        "😴 **BOT SLEEPING** 😴\n\n"
        "I have completed all pending tasks and will go dormant shortly.\n"
        "To wake me up instantly when you need me again, please click the link below."
    )
    
    # In a real implementation, 'reply_markup' is a structure containing the button.
    # We simulate the button's payload here.
    reply_markup = {
        "inline_keyboard": [
            [{"text": "🚀 Click to WAKE UP", "url": PUBLIC_URL}]
        ]
    }

    # 3. Send the new link
    new_message_id = api_send_inline_keyboard(chat_id, link_text, reply_markup)
    
    # 4. Save the new ID for future deletion
    set_config_value("LAST_LINK_MESSAGE_ID", new_message_id)
    LOGGER.info(f"WAKEUP LINK SENT: Saved new message ID {new_message_id} to config.")
    
    return new_message_id

# --- TASK EXECUTION MOCK ---

def simulate_task_execution(chat_id, message_id, text, is_large_file=False):
    """
    Simulates the core processing of a user-sent message.
    Handles cleanup, resource checks, and persistent failure logging.
    """
    
    # --- 1. RESOURCE/SAFETY CHECK ---
    if is_large_file:
        reason = f"RESOURCE EXHAUSTION BLOCK: Incoming file exceeds {MAX_FILE_SIZE_MB}MB safety limit."
        LOGGER.error(f"Task failed due to large file: ID:{message_id}")
        # Send an immediate, specific failure message
        api_send_message(chat_id, f"🛑 **FAILURE:** {reason}")
        return False

    # --- 2. CLEANUP ---
    cleaned_text = clean_message_text(text)
    
    # --- 3. SIMULATE PROCESSING ---
    LOGGER.info(f"Processing message {message_id}. Cleaned Content: '{cleaned_text[:50]}...'")
    
    # Randomly simulate a failure for demonstration (e.g., external API timeout)
    if random.random() < 0.1:  # 10% chance of failure
        reason = "Simulated External API Timeout or Processing Error."
        
        # PERSISTENT FAILURE LOGGING
        tasks = load_failed_tasks()
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tasks.append({
            "timestamp": timestamp,
            "chat_id": chat_id,
            "message_id": message_id,
            "reason": reason,
            "content_preview": cleaned_text[:30] + "..." if cleaned_text else "[No content]"
        })
        save_failed_tasks(tasks)
        
        LOGGER.warning(f"Task FAILED persistently: {reason}")
        api_send_message(chat_id, f"⚠️ **Task failed.** Reason: {reason}. It has been added to the `/failed` list.")
        return False

    # --- 4. SUCCESS RESULT ---
    
    # Simulate a delay for a long running task before success feedback
    time.sleep(random.uniform(1.0, 3.0)) 

    # Split the clean text into parts before sending the final result
    final_text = f"✅ **TASK COMPLETE**\nOriginal Content:\n\n{cleaned_text}"
    api_send_message(chat_id, final_text)
    
    # Send the wake-up link after the task is done (in the handler)
    return True


