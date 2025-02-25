from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, BaseHandler
import os
from dotenv import load_dotenv
import logging
from datetime import datetime
import json
import tempfile
import shutil
import sys

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Constants for data files
DATA_FILE = 'engagement_data.json'
HISTORY_FILE = 'engagement_history.json'

# Store engagement data per chat
engagement_data = {}
# Cache to store message senders: chat_id -> {message_id: user_id}
message_senders = {}

# Custom handler for message_reaction updates
class ReactionHandler(BaseHandler):
    def __init__(self, callback, block=True):
        super().__init__(callback, block=block)
        self.block = block

    def check_update(self, update):
        return hasattr(update, 'message_reaction') and update.message_reaction is not None

    async def handle_update(self, update, application, check_result, context):
        return await self.callback(update, context)

async def start(update: Update, context: CallbackContext):
    """Welcome message for the bot."""
    await update.message.reply_text(
        "👋 Hi! I'm tracking engagement in this chat.\n"
        "• Messages are counted\n"
        "• Reactions are counted\n"
        "Use /stats to see the leaderboard!"
    )

async def track_message(update: Update, context: CallbackContext):
    """Track messages and store sender information."""
    try:
        if not update.message or not update.message.from_user:
            return
            
        chat_id = str(update.message.chat.id)
        user_id = str(update.message.from_user.id)
        username = update.message.from_user.username or update.message.from_user.first_name
        message_id = update.message.message_id
        
        # Initialize data structures
        if chat_id not in engagement_data:
            engagement_data[chat_id] = {}
        if user_id not in engagement_data[chat_id]:
            engagement_data[chat_id][user_id] = {
                "username": username,
                "messages": 0,
                "reactions_given": 0,
                "reactions_received": 0,
                "total_points": 0
            }
        
        # Update counts
        engagement_data[chat_id][user_id]["messages"] += 1
        engagement_data[chat_id][user_id]["total_points"] += 1
        
        # Store message sender
        if chat_id not in message_senders:
            message_senders[chat_id] = {}
        message_senders[chat_id][message_id] = user_id
        
        # Save data after update
        save_data()
        
        logger.info(f"📝 Message from {username}")
        
    except Exception as e:
        logger.error(f"❌ Error tracking message: {e}")

async def track_reaction(update: Update, context: CallbackContext):
    """Track reactions."""
    try:
        reaction = update.message_reaction
        if not reaction or not reaction.user or reaction.user.is_bot:
            logger.info("Skipping reaction: missing data or from bot")
            return

        chat_id = str(reaction.chat.id)
        reactor_id = str(reaction.user.id)
        reactor_name = reaction.user.username or reaction.user.first_name
        message_id = reaction.message_id

        # Only count reactions that are added (not removed)
        if not reaction.new_reaction:
            logger.info(f"Reaction removed by {reactor_name}")
            return

        logger.info(f"Processing reaction from {reactor_name} in chat {chat_id}")

        # Initialize chat data if needed
        if chat_id not in engagement_data:
            engagement_data[chat_id] = {}

        # Initialize reactor data if needed
        if reactor_id not in engagement_data[chat_id]:
            engagement_data[chat_id][reactor_id] = {
                "username": reactor_name,
                "messages": 0,
                "reactions_given": 0,
                "reactions_received": 0,
                "total_points": 0
            }

        # Update reactor's stats
        engagement_data[chat_id][reactor_id]["reactions_given"] += 1
        engagement_data[chat_id][reactor_id]["total_points"] += 1

        # Try to update target's stats if we can find them
        if chat_id in message_senders and message_id in message_senders[chat_id]:
            target_id = message_senders[chat_id][message_id]
            if target_id in engagement_data[chat_id]:
                engagement_data[chat_id][target_id]["reactions_received"] += 1
                engagement_data[chat_id][target_id]["total_points"] += 1
                target_name = engagement_data[chat_id][target_id]["username"]
                logger.info(f"Credited reaction to {target_name}")

        # Add save after reaction updates
        save_data()
        logger.info("Reaction processed and data saved")

    except Exception as e:
        logger.error(f"Error tracking reaction: {e}", exc_info=True)

async def show_stats(update: Update, context: CallbackContext):
    """Show top 5 users by total points."""
    try:
        chat_id = str(update.message.chat.id)
        
        if chat_id not in engagement_data:
            await update.message.reply_text("No engagement recorded yet!")
            return
            
        # Sort users by total points
        sorted_users = sorted(
            engagement_data[chat_id].items(),
            key=lambda x: x[1]["total_points"],
            reverse=True
        )[:5]  # Only top 5
        
        text = "📊 Engagement Leaderboard\n\n"
        for i, (user_id, data) in enumerate(sorted_users, 1):
            text += f"{i}. @{data['username']} - Total points: {data['total_points']}\n"
        
        await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error showing stats: {e}")

async def show_admin_stats(update: Update, context: CallbackContext):
    """Show detailed stats for admins (top 25)."""
    try:
        chat_id = str(update.message.chat.id)
        user_id = str(update.message.from_user.id)
        
        # Check if user is admin
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("This command is only available to admins!")
            return
        
        if chat_id not in engagement_data:
            await update.message.reply_text("No engagement recorded yet!")
            return
            
        # Sort users by total points
        sorted_users = sorted(
            engagement_data[chat_id].items(),
            key=lambda x: x[1]["total_points"],
            reverse=True
        )[:25]  # Top 25 for admins
        
        text = "📊 Detailed Engagement Stats (Admin View)\n\n"
        for i, (user_id, data) in enumerate(sorted_users, 1):
            text += (
                f"{i}. @{data['username']}\n"
                f"   Points: {data['total_points']} "
                f"(Messages: {data['messages']}, "
                f"Reactions: +{data['reactions_given']}/-{data['reactions_received']})\n\n"
            )
        
        await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error showing admin stats: {e}")

async def show_history(update: Update, context: CallbackContext):
    """Show historical leaderboard data for admins."""
    try:
        chat_id = str(update.message.chat.id)
        user_id = str(update.message.from_user.id)
        
        # Check if user is admin
        chat_member = await context.bot.get_chat_member(chat_id, user_id)
        if chat_member.status not in ['administrator', 'creator']:
            await update.message.reply_text("This command is only available to admins!")
            return
        
        # Load history
        if not os.path.exists(HISTORY_FILE):
            await update.message.reply_text("No historical data available yet!")
            return
            
        with open(HISTORY_FILE, 'r') as f:
            history = json.load(f)
        
        # Get last month's data
        last_month = history.get('last_reset', 'No data')
        last_month_data = history.get(last_month, {}).get(chat_id, {})
        
        if not last_month_data:
            await update.message.reply_text("No data from last month!")
            return
        
        text = f"📊 Last Month's Top Users ({last_month})\n\n"
        
        # Sort and show top 10
        sorted_users = sorted(
            last_month_data.items(),
            key=lambda x: x[1]["total_points"],
            reverse=True
        )[:10]
        
        for i, (uid, data) in enumerate(sorted_users, 1):
            text += f"{i}. @{data['username']} - {data['total_points']} points\n"
        
        await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"Error showing history: {e}")

def save_data():
    """Save engagement data to file with atomic writes."""
    try:
        # Write to a temporary file first
        with tempfile.NamedTemporaryFile('w', delete=False) as temp_file:
            json.dump(engagement_data, temp_file, indent=2)
            temp_file.flush()
            os.fsync(temp_file.fileno())  # Ensure data is written to disk
            
        # Atomically replace the original file
        shutil.move(temp_file.name, DATA_FILE)
        logger.info("💾 Data saved successfully")
        
    except Exception as e:
        logger.error(f"Error saving data: {e}")
        if 'temp_file' in locals() and os.path.exists(temp_file.name):
            os.remove(temp_file.name)  # Clean up temp file on error

def load_data():
    """Load engagement data from file with detailed error logging."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                if not isinstance(data, dict):
                    raise ValueError("Loaded data is not a dictionary")
                logger.info(f"📂 Loaded data for {len(data)} chats")
                return data
                
        logger.info("No data file found, starting fresh")
        return {}
        
    except Exception as e:
        logger.error(f"Error loading data from {DATA_FILE}: {e}")
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, 'r') as f:
                    content = f.read()
                    logger.error(f"File content (first 100 chars): {content[:100]}...")
            except Exception as read_error:
                logger.error(f"Could not read file content: {read_error}")
        return {}

def check_monthly_reset():
    """Check and handle monthly reset."""
    try:
        current_month = datetime.now().strftime('%Y-%m')
        
        # Load current data
        current_data = load_data()
        if not current_data:
            return
            
        # Load historical data
        history = {}
        if os.path.exists(HISTORY_FILE):
            with open(HISTORY_FILE, 'r') as f:
                history = json.load(f)
        
        # Check if we need to reset
        data_month = history.get('last_reset', '2000-01')
        if current_month > data_month:
            # Save current data to history
            history['last_reset'] = current_month
            history[data_month] = current_data
            
            # Save history
            with open(HISTORY_FILE, 'w') as f:
                json.dump(history, f, indent=2)
            
            # Reset current data
            for chat_id in current_data:
                for user_id in current_data[chat_id]:
                    current_data[chat_id][user_id].update({
                        "messages": 0,
                        "reactions_given": 0,
                        "reactions_received": 0,
                        "total_points": 0
                    })
            
            # Save reset data
            save_data()
            logger.info(f"Monthly reset performed for {current_month}")
            
    except Exception as e:
        logger.error(f"Error in monthly reset: {e}")

def check_single_instance():
    """Ensure only one instance of the bot is running."""
    pid_file = "bot.pid"
    
    try:
        if os.path.exists(pid_file):
            with open(pid_file, 'r') as f:
                old_pid = f.read().strip()
                try:
                    # Check if process is still running
                    os.kill(int(old_pid), 0)
                    logger.error(f"Bot already running with PID {old_pid}")
                    sys.exit(1)
                except (ProcessLookupError, ValueError):
                    # Process not running, we can continue
                    pass
                    
        # Write current PID
        with open(pid_file, 'w') as f:
            f.write(str(os.getpid()))
            
    except Exception as e:
        logger.error(f"Error checking single instance: {e}")
        sys.exit(1)

def main():
    try:
        # Ensure single instance
        check_single_instance()
        
        # Load existing data
        global engagement_data
        engagement_data = load_data()
        
        # Set up application
        app = Application.builder().token(BOT_TOKEN).build()
        
        # Add handlers
        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("stats", show_stats))
        app.add_handler(CommandHandler("statsadmin", show_admin_stats))
        app.add_handler(CommandHandler("history", show_history))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
        app.add_handler(ReactionHandler(track_reaction, block=False))
        
        logger.info("🚀 Bot starting...")
        app.run_polling(
            allowed_updates=["message", "message_reaction"],
            drop_pending_updates=True
        )
        
    except Exception as e:
        logger.error(f"Error in main: {e}", exc_info=True)
        
    finally:
        # Save data before exit
        save_data()

if __name__ == '__main__':
    main()