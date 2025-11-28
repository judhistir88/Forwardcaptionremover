# Main entry point for the bot. Contains the infinite polling loop.

import time
import random
from config import LOGGER, validate_config
from handlers import handle_incoming_message, handle_callback_query
from utils import enforce_api_rate_limit

# --- SIMULATION DATA ---
# This simulates the different types of incoming JSON payloads from Telegram.
SIMULATED_MESSAGES = [
    # 1. Task with media (Photo/Video Only ON: PASS)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 100, "is_photo": True, "caption": "Awesome picture to process @source_user_handle"},
    
    # 2. Task with full hyperlink caption (Passes: protects command-like structure)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 101, "text": "[/run_task Process this link](https://test.com)"},

    # 3. Simple Command to get settings
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 102, "text": "/settings"},
    
    # 4. Command to toggle a setting via button click (simulated callback)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 103, "is_callback_query": True, "data": "toggle_photo_video"},

    # 5. Task with content to be cleaned (Clean: Passes)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 104, "text": "This item has Shared via Telegram and @test_bot_name. Please remove this."},
    
    # 6. Task that exceeds file size (Resource Exhaustion Block)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 105, "is_document": True, "is_large_file": True, "caption": "Very large document"},
    
    # 7. Task that will randomly fail (Persistence Check)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 106, "is_video": True, "caption": "Video content to process."},
    
    # 8. Command to check failed list
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 107, "text": "/failed"},

    # 9. Message type that should be ignored when filter is ON (Poll: Rejected)
    {"chat_id": -1001234567890, "from_user_id": 12345678, "message_id": 108, "is_poll": True, "poll_question": "What is your favorite color?"},

]

def simulate_polling_loop():
    """
    Simulates the bot's operation in a polling mode.
    In a real app, this would be an infinite loop calling getUpdates.
    """
    if not validate_config():
        LOGGER.critical("Bot terminated due to critical configuration errors.")
        return

    LOGGER.info("Bot started successfully. Entering simulated polling loop.")
    
    # Only run the simulated messages once for the example
    for i, update in enumerate(SIMULATED_MESSAGES):
        
        # 1. Simulate button click (callback query)
        if update.get("is_callback_query"):
            callback_query_data = {
                "chat_id": update["chat_id"],
                "data": update["data"],
                # Message ID is needed to know *which* message to edit the buttons on
                "message_id": 102 # Assuming the /settings message was ID 102 from the log
            }
            handle_callback_query(callback_query_data)
        
        # 2. Simulate standard message
        else:
            handle_incoming_message(update)
            
        # Simulate network delay between processing updates
        time.sleep(1)

    LOGGER.info("Simulated message queue processed. Bot would now sleep/go dormant.")


if __name__ == "__main__":
    simulate_polling_loop()
    


