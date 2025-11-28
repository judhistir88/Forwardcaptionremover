# Handles incoming messages, commands, and callback queries (button clicks) for Telegram bot.

from config import LOGGER, BOT_OWNER_ID, LOG_FILE, MAX_FILE_SIZE_MB
from utils import (
    get_config_value, set_config_value, load_failed_tasks, save_failed_tasks,
    generate_telegram_link, split_long_message, save_config, load_config
)
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
import os
from datetime import datetime

# --- CONFIGURATION KEY MAPPINGS ---
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
    """Extracts text content and flags from Telegram message."""
    text = message.text or message.caption or ""
    is_sticker = hasattr(message, "sticker") and message.sticker is not None
    is_photo = hasattr(message, "photo") and message.photo is not None
    is_video = hasattr(message, "video") and message.video is not None
    is_document = hasattr(message, "document") and message.document is not None
    is_large_file = (
        (is_document and message.document and message.document.file_size > MAX_FILE_SIZE_MB * 1024 * 1024)
        or (is_video and message.video and message.video.file_size > MAX_FILE_SIZE_MB * 1024 * 1024)
        or (is_photo and message.photo and message.photo[-1].file_size > MAX_FILE_SIZE_MB * 1024 * 1024)
    )
    return text, is_sticker, is_photo, is_video, is_document, is_large_file

# --- MESSAGE TYPE FILTERING (Resource Control) ---
def check_allowed_message_type(chat_id, is_sticker, is_photo, is_video, is_document, text, context):
    """Checks if the message type is allowed based on toggle settings."""
    # 1. STICKER BLOCK CHECK
    if is_sticker and get_config_value("STICKER_BLOCK_ENABLED"):
        context.bot.send_message(chat_id=chat_id,
                                text="🚫 Sticker processing is currently OFF. Please disable in /settings.")
        return False

    # 2. PHOTO/VIDEO ONLY CHECK
    if get_config_value("PHOTO_VIDEO_ONLY_ENABLED"):
        if is_photo or is_video:
            return True
        else:
            reason = "File/Video Only mode is ON. Ignoring non-photo/video content (e.g., text, document, poll, GIF)."
            if not text.startswith('/'):
                context.bot.send_message(chat_id=chat_id,
                                        text=f"🚫 **Filter Active:** {reason}")
            return False

    # 3. Allow all types otherwise
    return True

# --- COMMAND HANDLERS ---
async def send_settings_menu(chat_id, context: ContextTypes.DEFAULT_TYPE):
    """Sends the inline keyboard menu for settings."""
    config = get_config_value("STICKER_BLOCK_ENABLED")
    config_pv = get_config_value("PHOTO_VIDEO_ONLY_ENABLED")
    sticker_status = "ON" if config else "OFF"
    pv_status = "ON" if config_pv else "OFF"

    text = (
        "⚙️ **Bot Settings (Persistent)**\n"
        "Click a button to toggle the setting. The status updates instantly."
    )
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"Stickers: {sticker_status}", callback_data="toggle_stickers")],
        [InlineKeyboardButton(f"Photo/Video Only: {pv_status}", callback_data="toggle_photo_video")],
    ])
    await context.bot.send_message(chat_id=chat_id, text=text, reply_markup=keyboard)

async def send_failed_tasks_report(chat_id, context: ContextTypes.DEFAULT_TYPE):
    tasks = load_failed_tasks()
    if not tasks:
        await context.bot.send_message(chat_id, "🎉 **Failed Task List is Clean!** No tasks are awaiting manual retry.")
        return

    report = [f"⚠️ **FAILED TASKS REPORT ({len(tasks)} items)** ⚠️"]
    for i, task in enumerate(tasks):
        link = generate_telegram_link(task['chat_id'], task['message_id'])
        report.append(f"**{i + 1}. [{task['timestamp'][:19]}]** Reason: {task['reason']}")
        report.append(f"Content: `{task['content_preview']}`")
        report.append(f"🔗 [Click to Check Source Message]({link})\n")

    await context.bot.send_message(chat_id, "\n".join(report), parse_mode="Markdown")

def add_failed_task_manual(chat_id, content, context):
    tasks = load_failed_tasks()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks.append({
        "timestamp": timestamp,
        "chat_id": chat_id,
        "message_id": 0,
        "reason": "MANUAL ENTRY",
        "content_preview": content[:30] + "..."
    })
    save_failed_tasks(tasks)
    context.bot.send_message(chat_id, f"✅ Manual task added: `{content[:30]}...`")

def remove_failed_task(chat_id, index_str, context):
    try:
        index = int(index_str) - 1
        tasks = load_failed_tasks()
        if 0 <= index < len(tasks):
            removed_task = tasks.pop(index)
            save_failed_tasks(tasks)
            context.bot.send_message(chat_id, f"🗑️ Task #{index + 1} removed successfully. Reason: {removed_task['reason']}.")
        else:
            context.bot.send_message(
                chat_id, f"❌ Invalid index. Please use a number from the `/failed` list (1 to {len(tasks)})."
            )
    except ValueError:
        context.bot.send_message(chat_id, "❌ Invalid format. Please provide a valid number (e.g., `/remove_task 3`).")

async def send_cleanup_list(chat_id, context: ContextTypes.DEFAULT_TYPE):
    cleanup_strings = get_config_value("CLEANUP_STRINGS")
    if not cleanup_strings:
        await context.bot.send_message(chat_id, "🧹 **Cleanup List is Empty!** No phrases will be stripped.")
        return

    report = [f"🧹 **CURRENT CLEANUP STRINGS ({len(cleanup_strings)} items)** 🧹"]
    for i, phrase in enumerate(cleanup_strings):
        report.append(f"**{i + 1}.** `{phrase}`")

    await context.bot.send_message(chat_id, "\n".join(report), parse_mode="Markdown")

def add_cleanup_string(chat_id, phrase, context):
    config = load_config()
    config['CLEANUP_STRINGS'].append(phrase)
    save_config(config)
    context.bot.send_message(chat_id, f"✅ Cleanup string added: `{phrase}`")

def remove_cleanup_string(chat_id, index_str, context):
    try:
        index = int(index_str) - 1
        config = load_config()
        cleanup_list = config['CLEANUP_STRINGS']
        if 0 <= index < len(cleanup_list):
            removed_phrase = cleanup_list.pop(index)
            save_config(config)
            context.bot.send_message(chat_id, f"🗑️ Cleanup string #{index + 1} removed: `{removed_phrase}`.")
        else:
            context.bot.send_message(
                chat_id,
                f"❌ Invalid index. Use a number from the `/list_cleanup` list (1 to {len(cleanup_list)})."
            )
    except ValueError:
        context.bot.send_message(chat_id, "❌ Invalid format. Please provide a valid number (e.g., `/remove_cleanup 2`).")

async def send_log_file(chat_id, context: ContextTypes.DEFAULT_TYPE):
    try:
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            log_content = "".join(lines[-1000:])
        await context.bot.send_document(chat_id, document=log_content, filename=os.path.basename(LOG_FILE))
    except FileNotFoundError:
        await context.bot.send_message(chat_id, "❌ Log file not found.")
    except Exception as e:
        LOGGER.error(f"Error reading log file: {e}")
        await context.bot.send_message(chat_id, f"❌ An error occurred while fetching the log: {e}")

async def handle_incoming_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    chat_id = message.chat.id if hasattr(message, "chat") else message.from_user.id
    from_user_id = message.from_user.id if hasattr(message, "from_user") else None

    # --- SECURITY CHECK ---
    if str(from_user_id) != str(BOT_OWNER_ID):
        await context.bot.send_message(chat_id, "🔒 Unauthorized access denied.")
        return

    text, is_sticker, is_photo, is_video, is_document, is_large_file = safely_extract_content(message)
    command = text.split()[0].lower() if text and text.startswith('/') else None

    # --- Resource and message type filter ---
    if not check_allowed_message_type(chat_id, is_sticker, is_photo, is_video, is_document, text, context):
        return

    if is_large_file:
        context.bot.send_message(
            chat_id, f"🛑 **FAILURE:** Incoming file exceeds {MAX_FILE_SIZE_MB}MB safety limit."
        )
        add_failed_task_manual(chat_id, text or "LARGE FILE BLOCKED", context)
        return

    # --- COMMAND ROUTING ---
    # The following handles all bot commands and messages
    if command in ["/start", "/help"]:
        config = load_config()
        status_pv = "ON" if config.get('PHOTO_VIDEO_ONLY_ENABLED') else "OFF"
        status_sticker = "ON" if config.get('STICKER_BLOCK_ENABLED') else "OFF"
        welcome_text = (
            "🤖 **Private Bot Status**\n\n"
            f"**File Filter:** `{status_pv}` (Only Photo/Video allowed)\n"
            f"**Sticker Block:** `{status_sticker}`\n"
            f"**Cleanup Phrases:** `{len(config.get('CLEANUP_STRINGS', []))}`\n\n"
            "--- **Commands** ---\n"
            "- `/run_task [content]`\n"
            "- `/finish` (Sends cleanup confirmation)\n"
            "- `/settings` (Manage toggles)\n"
            "- `/failed` (Retry list)\n"
            "- `/list_cleanup` / `/add_cleanup`\n"
            "- `/log`\n"
            "- `/help`"
        )
        await context.bot.send_message(chat_id, welcome_text)
    elif command == "/settings":
        await send_settings_menu(chat_id, context)
    elif command == "/run_task":
        # Implement your processing logic here
        await context.bot.send_message(chat_id, "✅ Run Task: Processed!")
    elif command == "/finish":
        await context.bot.send_message(chat_id, "Batch complete. I'm now awaiting new tasks or going dormant.")
    elif command == "/log":
        await send_log_file(chat_id, context)
    elif command == "/failed":
        await send_failed_tasks_report(chat_id, context)
    elif command == "/add_task":
        content = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if content:
            add_failed_task_manual(chat_id, content, context)
        else:
            await context.bot.send_message(chat_id, "❌ Usage: `/add_task [content]`")
    elif command == "/remove_task":
        index_str = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if index_str:
            remove_failed_task(chat_id, index_str, context)
        else:
            await context.bot.send_message(chat_id, "❌ Usage: `/remove_task [number]`")
    elif command == "/list_cleanup":
        await send_cleanup_list(chat_id, context)
    elif command == "/add_cleanup":
        phrase = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if phrase:
            add_cleanup_string(chat_id, phrase, context)
        else:
            await context.bot.send_message(chat_id, "❌ Usage: `/add_cleanup [phrase to remove]`")
    elif command == "/remove_cleanup":
        index_str = text.split(maxsplit=1)[1] if len(text.split()) > 1 else None
        if index_str:
            remove_cleanup_string(chat_id, index_str, context)
        else:
            await context.bot.send_message(chat_id, "❌ Usage: `/remove_cleanup [number]`")
    else:
        # If just text, process as a task
        await context.bot.send_message(chat_id, "✅ Message/task processed.")

async def handle_callback_query(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if not query or not query.data:
        return

    chat_id = query.message.chat.id
    data = query.data
    config_key = SETTINGS_MAP.get(data, {}).get("key")
    if not config_key:
        await query.answer("Unknown setting")
        return

    # Toggle the config value
    current = get_config_value(config_key)
    set_config_value(config_key, not current)
    await query.answer(text=f"{SETTINGS_MAP[data]['name']} set to {'ON' if not current else 'OFF'}")
    # Refresh the menu
    await send_settings_menu(chat_id, context)