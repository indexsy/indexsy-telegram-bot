from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext, BaseHandler
import os
from dotenv import load_dotenv
import logging

# Setup logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

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

        logger.info("Reaction processed successfully")

    except Exception as e:
        logger.error(f"Error tracking reaction: {e}", exc_info=True)

async def show_stats(update: Update, context: CallbackContext):
    """Show engagement stats."""
    try:
        chat_id = str(update.message.chat.id)
        
        if chat_id not in engagement_data:
            await update.message.reply_text("No engagement recorded yet!")
            return
            
        text = "📊 Engagement Stats:\n\n"
        
        # Sort users by total points
        sorted_users = sorted(
            engagement_data[chat_id].items(),
            key=lambda x: x[1]["total_points"],
            reverse=True
        )
        
        for user_id, data in sorted_users:
            text += (
                f"@{data['username']}:\n"
                f"• Messages: {data['messages']}\n"
                f"• Reactions Given: {data['reactions_given']}\n"
                f"• Reactions Received: {data['reactions_received']}\n"
                f"• Total Points: {data['total_points']}\n\n"
            )
        
        await update.message.reply_text(text)
        
    except Exception as e:
        logger.error(f"❌ Error showing stats: {e}")

def main():
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("stats", show_stats))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    app.add_handler(ReactionHandler(track_reaction, block=False))
    
    logger.info("🚀 Bot starting...")
    app.run_polling(
        allowed_updates=["message", "message_reaction"],
        drop_pending_updates=True
    )

if __name__ == '__main__':
    main()