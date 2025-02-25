from telegram import Update
from telegram.ext import (
    Application, 
    CommandHandler, 
    MessageHandler, 
    filters, 
    CallbackContext,
    ChatMemberHandler
)
import json
import os
from dotenv import load_dotenv
import logging
import sys

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

# Add file handler separately
file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
file_handler.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Store engagement data in a JSON file
ENGAGEMENT_FILE = 'engagement_data.json'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize or load engagement data
def load_engagement_data():
    try:
        if os.path.exists(ENGAGEMENT_FILE):
            with open(ENGAGEMENT_FILE, 'r') as f:
                return json.load(f)
    except Exception as e:
        logger.error(f"Error loading engagement data: {e}")
    return {}

def save_engagement_data(data):
    try:
        with open(ENGAGEMENT_FILE, 'w') as f:
            json.dump(data, f)
    except Exception as e:
        logger.error(f"Error saving engagement data: {e}")

engagement_data = load_engagement_data()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 Welcome to the Engagement Bot!\n"
        "I track user engagement through comments and reactions.\n"
        "Use /leaderboard to see the top users."
    )

async def track_message(update: Update, context: CallbackContext):
    try:
        if not update.message or not update.message.from_user:
            logger.info("Skipping: No message or user data")
            return
        
        chat_id = str(update.message.chat.id)
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.username or update.message.from_user.first_name
        message_text = update.message.text
        
        logger.info(f"Processing message: '{message_text[:30]}...' from {username} in chat {chat_id}")
        
        if chat_id not in engagement_data:
            logger.info(f"Creating new chat data for {chat_id}")
            engagement_data[chat_id] = {}
        
        if user_id not in engagement_data[chat_id]:
            logger.info(f"Creating new user data for {username}")
            engagement_data[chat_id][user_id] = {
                "username": username,
                "points": 0,
                "messages": 0,
                "reactions_given": 0,
                "reactions_received": 0
            }
        
        engagement_data[chat_id][user_id]["messages"] += 1
        engagement_data[chat_id][user_id]["points"] += 1
        save_engagement_data(engagement_data)
        
        logger.info(f"Updated stats for {username}: messages={engagement_data[chat_id][user_id]['messages']}, points={engagement_data[chat_id][user_id]['points']}")
        
    except Exception as e:
        logger.error(f"Error in track_message: {e}", exc_info=True)

async def track_reaction(update: Update, context: CallbackContext):
    try:
        logger.info(f"Received update type: {type(update)}")
        logger.info(f"Update content: {update}")
        
        if not hasattr(update, 'message_reaction'):
            logger.info("No message_reaction in update")
            return
        
        chat_id = str(update.message_reaction.chat.id)
        reactor = update.message_reaction.user
        message = update.message_reaction.message
        
        logger.info(f"Processing reaction in chat {chat_id}")
        logger.info(f"Reactor: {reactor.username if reactor else 'Unknown'}")
        logger.info(f"Message: {message.text[:30] if message and message.text else 'No text'}")
        
        if not reactor or not message or not message.from_user:
            logger.info("Missing user data in reaction")
            return
            
        target_user = message.from_user
        
        logger.info(f"Processing reaction in chat {chat_id}")
        
        if chat_id not in engagement_data:
            engagement_data[chat_id] = {}
        
        # Process both reactor and target
        for user, is_reactor in [(reactor, True), (target_user, False)]:
            user_id = str(user.id)
            username = user.username or user.first_name
            
            if user_id not in engagement_data[chat_id]:
                engagement_data[chat_id][user_id] = {
                    "username": username,
                    "points": 0,
                    "messages": 0,
                    "reactions_given": 0,
                    "reactions_received": 0
                }
            
            if is_reactor:
                engagement_data[chat_id][user_id]["reactions_given"] += 1
            else:
                engagement_data[chat_id][user_id]["reactions_received"] += 1
            engagement_data[chat_id][user_id]["points"] += 1
        
        save_engagement_data(engagement_data)
        
    except Exception as e:
        logger.error(f"Error in track_reaction: {e}")

async def show_leaderboard(update: Update, context: CallbackContext):
    try:
        chat_id = str(update.message.chat.id)
        
        if chat_id not in engagement_data:
            engagement_data[chat_id] = {}
        
        chat_data = engagement_data[chat_id]
        sorted_users = sorted(
            chat_data.items(),
            key=lambda x: x[1]["points"],
            reverse=True
        )[:10]
        
        leaderboard_text = "🏆 Engagement Leaderboard 🏆\n\n"
        for i, (user_id, data) in enumerate(sorted_users, 1):
            leaderboard_text += (
                f"{i}. @{data['username']}\n"
                f"   Points: {data['points']} "
                f"(Messages: {data['messages']}, "
                f"Reactions Given: {data.get('reactions_given', 0)}, "
                f"Received: {data.get('reactions_received', 0)})\n"
            )
        
        if not sorted_users:
            leaderboard_text += "No engagement recorded yet!"
        
        await update.message.reply_text(leaderboard_text)
        
    except Exception as e:
        logger.error(f"Error in show_leaderboard: {e}")

async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Error occurred: {context.error}")

async def debug_chat_id(update: Update, context: CallbackContext):
    try:
        logger.info("Debug command received")
        
        if not update.message:
            logger.error("No message in debug update")
            return
            
        chat = update.message.chat
        user = update.message.from_user
        
        debug_info = (
            f"🔍 Debug Information:\n\n"
            f"Chat ID: {chat.id}\n"
            f"Chat Type: {chat.type}\n"
            f"Chat Title: {chat.title or 'N/A'}\n"
            f"User ID: {user.id}\n"
            f"Username: @{user.username or 'N/A'}"
        )
        
        logger.info(f"Debug info: {debug_info}")
        await update.message.reply_text(debug_info)
        
    except Exception as e:
        logger.error(f"Error in debug command: {e}", exc_info=True)

def check_single_instance():
    pid_file = "bot.pid"
    
    if os.path.exists(pid_file):
        with open(pid_file, 'r') as f:
            old_pid = f.read().strip()
            try:
                # Check if process still exists
                os.kill(int(old_pid), 0)
                logger.error(f"Bot is already running with PID {old_pid}")
                sys.exit(1)
            except OSError:
                pass
    
    # Write current PID
    with open(pid_file, 'w') as f:
        f.write(str(os.getpid()))

def main():
    try:
        check_single_instance()
        
        app = Application.builder().token(BOT_TOKEN).build()
        
        logger.info("Setting up command handlers...")
        
        # Add handlers with logging
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("leaderboard", show_leaderboard))
        app.add_handler(CommandHandler("debug", debug_chat_id))
        
        logger.info("Setting up message handlers...")
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
        
        logger.info("Setting up reaction handler...")
        app.add_handler(MessageHandler(filters.ALL & ~filters.TEXT & ~filters.COMMAND, track_reaction))
        
        logger.info("Bot starting...")
        app.run_polling(
            allowed_updates=["message", "message_reaction", "edited_message", "channel_post", "callback_query"],
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)

if __name__ == '__main__':
    main() 