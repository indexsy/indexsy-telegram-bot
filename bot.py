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

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG
)

# Add file handler separately
file_handler = logging.FileHandler('bot.log')
file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)

# Load environment variables
load_dotenv()

# Debug print
print("Bot token:", os.getenv('TELEGRAM_BOT_TOKEN'))

# Store engagement data in a JSON file
ENGAGEMENT_FILE = 'engagement_data.json'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Add at the top with other constants
ALLOWED_CHAT_ID = -1001234567890  # Replace with your channel's ID

# Initialize or load engagement data
def load_engagement_data():
    if os.path.exists(ENGAGEMENT_FILE):
        with open(ENGAGEMENT_FILE, 'r') as f:
            return json.load(f)
    return {}  # Empty dict for all chats

def save_engagement_data(data):
    with open(ENGAGEMENT_FILE, 'w') as f:
        json.dump(data, f)

engagement_data = load_engagement_data()

async def start(update: Update, context: CallbackContext):
    await update.message.reply_text(
        "👋 Welcome to the Engagement Bot!\n"
        "I track user engagement through comments and reactions.\n"
        "Use /leaderboard to see the top users."
    )

async def track_message(update: Update, context: CallbackContext):
    logger.info("========== NEW MESSAGE EVENT ==========")
    
    if not update.message or not update.message.from_user:
        logger.info("No message or user data")
        return
    
    chat_id = str(update.message.chat.id)
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or update.message.from_user.first_name
    
    logger.info(f"Message from: {username} in chat: {chat_id}")
    
    # Initialize chat data if it doesn't exist
    if chat_id not in engagement_data:
        engagement_data[chat_id] = {}
    
    if user_id not in engagement_data[chat_id]:
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
    
    logger.info(f"Added point for message from {username}")
    logger.info(f"Current points: {engagement_data[chat_id][user_id]['points']}")

async def track_reaction(update: Update, context: CallbackContext):
    logger.info("========== NEW REACTION EVENT ==========")
    logger.info(f"Update: {update}")
    
    if not hasattr(update, 'message_reaction'):
        logger.info("Not a message reaction")
        return
    
    reaction = update.message_reaction
    logger.info(f"Reaction: {reaction}")
    logger.info(f"Chat ID: {reaction.chat.id}")
    logger.info(f"Message ID: {reaction.message_id}")
    logger.info(f"User: {reaction.user.username if reaction.user else 'Unknown'}")
    
    try:
        # Process new reaction
        if not reaction.user or not reaction.message or not reaction.message.from_user:
            logger.info("Missing user data")
            return
            
        target_user = reaction.message.from_user
        
        # Initialize chat data
        if reaction.chat.id not in engagement_data:
            engagement_data[reaction.chat.id] = {}
        
        # Process reaction
        for user, is_reactor in [(reaction.user, True), (target_user, False)]:
            user_id = str(user.id)
            if user_id not in engagement_data[reaction.chat.id]:
                engagement_data[reaction.chat.id][user_id] = {
                    "username": user.username or user.first_name,
                    "points": 0,
                    "messages": 0,
                    "reactions_given": 0,
                    "reactions_received": 0
                }
            
            if is_reactor:
                engagement_data[reaction.chat.id][user_id]["reactions_given"] += 1
            else:
                engagement_data[reaction.chat.id][user_id]["reactions_received"] += 1
            engagement_data[reaction.chat.id][user_id]["points"] += 1
        
        save_engagement_data(engagement_data)
        logger.info(f"Successfully recorded reaction")
        logger.info("\n=== Processing Reaction ===")
        logger.info(f"Adding points for reaction from {reaction.user.username} to message by {target_user.username}")
    
    except Exception as e:
        logger.error(f"\n=== Error Processing Reaction ===\n{str(e)}\n{type(e)}")

async def show_leaderboard(update: Update, context: CallbackContext):
    chat_id = str(update.message.chat.id)
    
    # Initialize chat data if it doesn't exist
    if chat_id not in engagement_data:
        engagement_data[chat_id] = {}
    
    # Get chat-specific data
    chat_data = engagement_data[chat_id]
    
    sorted_users = sorted(
        chat_data.items(),
        key=lambda x: x[1]["points"],
        reverse=True
    )[:10]  # Top 10 users
    
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

async def error_handler(update: Update, context: CallbackContext):
    logger.error(f"Error occurred: {context.error}")

async def debug_chat_id(update: Update, context: CallbackContext):
    chat = update.message.chat
    logger.info(f"Chat ID: {chat.id}")
    logger.info(f"Chat Type: {chat.type}")
    logger.info(f"Chat Title: {chat.title}")
    await update.message.reply_text(f"Chat ID: {chat.id}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(CommandHandler("debug", debug_chat_id))
    
    # Add message handler
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    
    # Use MessageHandler with ALL filter for reactions
    app.add_handler(MessageHandler(
        filters.ALL & ~filters.TEXT & ~filters.COMMAND,
        track_reaction
    ))
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    logger.info("Bot starting...")
    app.run_polling(
        allowed_updates=["message", "message_reaction"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main() 