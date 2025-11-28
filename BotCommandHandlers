# Handles incoming messages, commands, and callback queries (button clicks).

import time
import os
import sys
from config import LOGGER, BOT_OWNER_ID, LOG_FILE, MAX_FILE_SIZE_MB
from api_mock import (
    api_send_message, api_send_document, api_leave_chat,
    simulate_task_execution, api_send_inline_keyboard, api_edit_message_reply_markup,
    send_wake_up_link
)
from utils import (
    get_config_value, set_config_value, load_failed_tasks, save_failed_tasks,
    generate_telegram_link, split_long_message, get_config_value
)

# --- CONFIGURATION KEY MAPPINGS ---
# Maps callback data to configuration keys and display names
SETTINGS_MAP = {
    "toggle_stickers": {
        "key": "STICKER_BLOCK_ENABLED",
        "name": "Stickers"
    },
    "toggle_photo_video": {
        "key": "PHOTO_VIDEO_ONLY_ENABLED",
        "name": "Photo/Video Only"
    }
}

# --- DEFENSIVE ATTRIBUTE ACCESS (Risk Mitigation) ---

def safely_extract_content(message):
    """Safely extracts text content from various message types without crashing."""
    if not message:
        return "", False, False, False, False

    text = ""
    is_sticker = message.get("is_sticker", False)
    is_large_file = message.get("is_large_file", False)
    is_photo = message.get("is_photo", False)
    is_video = message.get("is_video", False)
    is_document = message.get("is_document", False)
    is_poll = message.get("is_poll", False)

    # 1. Try to get caption (media/files)
    if 'caption' in message and message['caption']:
        text = message['caption']
    # 2. Try to get main text (plain text/commands)
    elif 'text' in message and message['text']:
        text = message['text']
    # 3. Try to get poll question
    elif is_poll and 'poll_question' in message:
        text = message['poll_question']

    return text, is_sticker, is_photo, is_video, is_document, is_large_file

# --- MESSAGE TYPE FILTERING (Resource Control) ---

def check_allowed_message_type(message, is_sticker, is_photo, is_video, is_document, text):
    """
    Checks if the message type is allowed based on persistent toggle settings.
    Returns True if allowed, False if rejected.
    """
    chat_id = message.get("chat_id")
    
    # 1. STICKER BLOCK CHECK (Priority 1: Always check for stickers)
    if is_sticker and get_config_value("STICKER_BLOCK_ENABLED"):
        api_send_message(chat_id, "🚫 Sticker processing is currently OFF. Please disable in /settings.")
        return False

    # 2. PHOTO/VIDEO ONLY CHECK (Priority 2: If ON, enforce strict media whitelist)
    if get_config_value("PHOTO_VIDEO_ONLY_ENABLED"):
        # Custom rule: Only allow Photo or Video. Reject everything else including Documents/Files.
        if is_photo or is_video:
            return True
        else:
            reason = "File/Video Only mode is ON. Ignoring non-photo/video content (e.g., text, document, poll, GIF)."
            # Only send a rejection message if the message is *not* a simple command
            if not text.startswith('/'):
                api_send_message(chat_id, f"🚫 **Filter Active:** {reason}")
            return False

    # 3. If both filters are OFF, allow all types
    return True

# --- COMMAND HANDLERS ---

def send_settings_menu(chat_id):
    """Sends the inline keyboard menu for settings."""
    config = get_config_value("STICKER_BLOCK_ENABLED")
    config_pv = get_config_value("PHOTO_VIDEO_ONLY_ENABLED")

    sticker_status = "ON" if config else "OFF"
    pv_status = "ON" if config_pv else "OFF"

    text = (
        "⚙️ **Bot Settings (Persistent)**\n"
        "Click a button to toggle the setting. The status updates instantly."
    )

    # Dynamically build the keyboard with current status
    reply_markup = {
        "inline_keyboard": [
            [{"text": f"Stickers: {sticker_status}", "callback_data": "toggle_stickers"}],
            [{"text": f"Photo/Video Only: {pv_status}", "callback_data": "toggle_photo_video"}]
        ]
    }
    
    # The message ID is important for editing the markup later
    message_id = api_send_inline_keyboard(chat_id, text, reply_markup)
    return message_id

def send_failed_tasks_report(chat_id):
    """Generates and sends the report of failed tasks with source links."""
    tasks = load_failed_tasks()
    if not tasks:
        api_send_message(chat_id, "🎉 **Failed Task List is Clean!** No tasks are awaiting manual retry.")
        return

    report = [f"⚠️ **FAILED TASKS REPORT ({len(tasks)} items)** ⚠️"]
    for i, task in enumerate(tasks):
        link = generate_telegram_link(task['chat_id'], task['message_id'])
        
        # Use link inside markdown for clickable text
        report.append(f"**{i + 1}. [{task['timestamp'][:19]}]** Reason: {task['reason']}")
        report.append(f"Content: `{task['content_preview']}`")
        report.append(f"🔗 [Click to Check Source Message]({link})\n")

    api_send_message(chat_id, "\n".join(report))

def add_failed_task_manual(chat_id, content):
    """Manually adds a task to the persistent failed list."""
    tasks = load_failed_tasks()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    tasks.append({
        "timestamp": timestamp,
        "chat_id": chat_id, # Use current chat ID for current context
        "message_id": 0, # Use 0 for manual entries since there is no source message
        "reason": "MANUAL ENTRY",
        "content_preview": content[:30] + "..."
    })
    save_failed_tasks(tasks)
    api_send_message(chat_id, f"✅ Manual task added: `{content[:30]}...`")

def remove_failed_task(chat_id, index_str):
    """Removes a task from the persistent list by index."""
    try:
        index = int(index_str) - 1
        tasks = load_failed_tasks()
        if 0 <= index < len(tasks):
            removed_task = tasks.pop(index)
            save_failed_tasks(tasks)
            api_send_message(chat_id, f"🗑️ Task #{index + 1} removed successfully. Reason: {removed_task['reason']}.")
        else:
            api_send_message(chat_id, f"❌ Invalid index. Please use a number from the `/failed` list (1 to {len(tasks)}).")
    except ValueError:
        api_send_message(chat_id, "❌ Invalid format. Please provide a valid number (e.g., `/remove_task 3`).")

def send_cleanup_list(chat_id):
    """Generates and sends the current cleanup string list."""
    cleanup_strings = get_config_value("CLEANUP_STRINGS")
    if not cleanup_strings:
        api_send_message(chat_id, "🧹 **Cleanup List is Empty!** No phrases will be stripped.")
        return

    report = [f"🧹 **CURRENT CLEANUP STRINGS ({len(cleanup_strings)} items)** 🧹"]
    for i, phrase in enumerate(cleanup_strings):
        report.append(f"**{i + 1}.** `{phrase}`")

    api_send_message(chat_id, "\n".join(report))

def add_cleanup_string(chat_id, phrase):
    """Adds a new cleanup string to the persistent list."""
    config = load_config()
    config['CLEANUP_STRINGS'].append(phrase)
    save_config(config)
    api_send_message(chat_id, f"✅ Cleanup string added: `{phrase}`")

def remove_cleanup_string(chat_id, index_str):
    """Removes a cleanup string from the persistent list by index."""
    try:
        index = int(index_str) - 1
        config = load_config()
        cleanup_list = config['CLEANUP_STRINGS']
        
        if 0 <= index < len(cleanup_list):
            removed_phrase = cleanup_list.pop(index)
            save_config(config)
            api_send_message(chat_id, f"🗑️ Cleanup string #{index + 1} removed: `{removed_phrase}`.")
        else:
            api_send_message(chat_id, f"❌ Invalid index. Use a number from the `/list_cleanup` list (1 to {len(cleanup_list)}).")
    except ValueError:
        api_send_message(chat_id, "❌ Invalid format. Please provide a valid number (e.g., `/remove_cleanup 2`).")

def send_log_file(chat_id):
    """Reads the log file and sends it as a document."""
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            # Send the last 1000 lines
            log_content = "".join(lines[-1000:])
            
            # Since the API is mocked, we simulate sending the file
            api_send_document(chat_id, log_content, os.path.basename(LOG_FILE))
            
    except FileNotFoundError:
        api_send_message(chat_id, "❌ Log file not found.")
    except Exception as e:
        LOGGER.error(f"Error reading log file: {e}")
        api_send_message(chat_id, f"❌ An error occurred while fetching the log: {e}")

# --- MAIN ROUTER ---

def handle_incoming_message(message):
    """Routes incoming messages (commands, text, media) to the appropriate handler."""
    chat_id = message.get("chat_id")
    from_user_id = message.get("from_user_id")
    
    # 1. SECURITY CHECK (Critical for private bot)
    if str(from_user_id) != str(BOT_OWNER_ID):
        api_send_message(chat_id, "🔒 Unauthorized access denied.")
        api_leave_chat(chat_id)
        return

    # --- 2. DEFENSIVE CONTENT EXTRACTION & FILTERING ---
    # Safely extract all possible content attributes
    text, is_sticker, is_photo, is_video, is_document, is_large_file = safely_extract_content(message)
    command = text.split()[0].lower() if text.startswith('/') else None
    
    # Check if the content is allowed based on toggles
    if not check_allowed_message_type(message, is_sticker, is_photo, is_video, is_document, text):
        return

    # Check for resource exhaustion before execution
    if is_large_file:
        simulate_task_execution(chat_id, message.get("message_id"), text, is_large_file=True)
        return

    # --- 3. COMMAND ROUTING ---
    if command == '/start':
        config = load_config()
        status_pv = "ON" if config['PHOTO_VIDEO_ONLY_ENABLED'] else "OFF"
        status_sticker = "ON" if config['STICKER_BLOCK_ENABLED'] else "OFF"

        welcome_text = (
            "🤖 **Private Bot Status**\n\n"
            f"**File Filter:** `{status_pv}` (Only Photo/Video allowed)\n"
            f"**Sticker Block:** `{status_sticker}`\n"
            f"**Cleanup Phrases:** `{len(config['CLEANUP_STRINGS'])}`\n\n"
            "--- **Commands** ---\n"
            "- `/run_task [content]`\n"
            "- `/finish` (Sends cleanup confirmation)\n"
            "- `/settings` (Manage toggles)\n"
            "- `/failed` (Retry list)\n"
            "- `/list_cleanup` / `/add_cleanup`\n"
            "- `/log`"
        )
        api_send_message(chat_id, welcome_text)

    elif command == '/settings':
        send_settings_menu(chat_id)

    elif command == '/run_task':
        # Everything not a command or an ignored type is treated as a task
        simulate_task_execution(chat_id, message.get("message_id"), text)
        send_wake_up_link(chat_id)

    elif command == '/finish':
        api_send_message(chat_id, "Batch complete. I'm now awaiting new tasks or going dormant.")
        send_wake_up_link(chat_id)

    elif command == '/log':
        send_log_file(chat_id)
    
    elif command == '/failed':
        send_failed_tasks_report(chat_id)
    
    elif command == '/add_task':
        content = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if content:
            add_failed_task_manual(chat_id, content)
        else:
            api_send_message(chat_id, "❌ Usage: `/add_task [content]`")

    elif command == '/remove_task':
        index_str = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if index_str:
            remove_failed_task(chat_id, index_str)
        else:
            api_send_message(chat_id, "❌ Usage: `/remove_task [number]`")

    elif command == '/list_cleanup':
        send_cleanup_list(chat_id)

    elif command == '/add_cleanup':
        phrase = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if phrase:
            add_cleanup_string(chat_id, phrase)
        else:
            api_send_message(chat_id, "❌ Usage: `/add_cleanup [phrase to remove]`")

    elif command == '/remove_cleanup':
        index_str = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if index_str:
            remove_cleanup_string(chat_id, index_str)
        else:
            api_send_message(chat_id, "❌ Usage: `/remove_cleanup [number]`")

    elif command and text.startswith('/'):
        # If it's a command not recognized
        api_send_message(chat_id, "❓ Unknown command. Use `/start` to see available commands.")
    
    elif text and not text.startswith('/'):
        # If it's just regular text and not a command, treat it as a task
        simulate_task_execution(chat_id, message.get("message_id"), text)
        send_wake_up_link(chat_id)


def handle_callback_query(callback_query):
    """Handles button clicks (callback queries) from the settings menu."""
    chat_id = callback_query.get("chat_id")
    callback_data = callback_query.get("data")
    message_id = callback_query.get("message_id")
    
    if callback_data in SETTINGS_MAP:
        mapping = SETTINGS_MAP[callback_data]
        key = mapping["key"]
        
        # 1. Toggle the persistent state
        current_state = get_config_value(key)
        new_state = not current_state
        set_config_value(key, new_state)
        
        # 2. Re-send the settings menu with the updated button state
        # (Editing the markup is simulated here by resending the menu structure)
        
        # First, rebuild the markup based on the new state
        config_pv = get_config_value("PHOTO_VIDEO_ONLY_ENABLED")
        config_sticker = get_config_value("STICKER_BLOCK_ENABLED")

        reply_markup = {
            "inline_keyboard": [
                [{"text": f"Stickers: {'ON' if config_sticker else 'OFF'}", "callback_data": "toggle_stickers"}],
                [{"text": f"Photo/Video Only: {'ON' if config_pv else 'OFF'}", "callback_data": "toggle_photo_video"}]
            ]
        }
        
        # Simulate editing the message to update the buttons
        api_edit_message_reply_markup(chat_id, message_id, reply_markup)

        status_text = "ON" if new_state else "OFF"
        api_send_message(chat_id, f"✅ Setting `{mapping['name']}` is now **{status_text}**.")
        LOGGER.info(f"Setting '{mapping['name']}' toggled to {status_text}.")
    else:
        api_send_message(chat_id, "❓ Unknown button action.")


