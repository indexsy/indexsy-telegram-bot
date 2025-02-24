from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import json
import os
from dotenv import load_dotenv

# Load environment variables lol
load_dotenv()

# Store engagement data in a JSON file
ENGAGEMENT_FILE = 'engagement_data.json'
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')

# Initialize or load engagement data
def load_engagement_data():
    if os.path.exists(ENGAGEMENT_FILE):
        with open(ENGAGEMENT_FILE, 'r') as f:
            return json.load(f)
    return {}

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
    user_id = str(update.message.from_user.id)
    username = update.message.from_user.username or update.message.from_user.first_name
    
    if user_id not in engagement_data:
        engagement_data[user_id] = {
            "username": username,
            "points": 0,
            "messages": 0,
            "reactions": 0
        }
    
    engagement_data[user_id]["messages"] += 1
    engagement_data[user_id]["points"] += 1
    save_engagement_data(engagement_data)

async def track_reaction(update: Update, context: CallbackContext):
    if update.message.reactions:
        for reaction in update.message.reactions:
            user_id = str(reaction.user.id)
            username = reaction.user.username or reaction.user.first_name
            
            if user_id not in engagement_data:
                engagement_data[user_id] = {
                    "username": username,
                    "points": 0,
                    "messages": 0,
                    "reactions": 0
                }
            
            engagement_data[user_id]["reactions"] += 1
            engagement_data[user_id]["points"] += 1
            save_engagement_data(engagement_data)

async def show_leaderboard(update: Update, context: CallbackContext):
    sorted_users = sorted(
        engagement_data.items(),
        key=lambda x: x[1]["points"],
        reverse=True
    )[:10]  # Top 10 users
    
    leaderboard_text = "🏆 Engagement Leaderboard 🏆\n\n"
    for i, (user_id, data) in enumerate(sorted_users, 1):
        leaderboard_text += (
            f"{i}. @{data['username']}\n"
            f"   Points: {data['points']} "
            f"(Messages: {data['messages']}, Reactions: {data['reactions']})\n"
        )
    
    await update.message.reply_text(leaderboard_text)

def main():
    # Use bot token from environment variable
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Add handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("leaderboard", show_leaderboard))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, track_message))
    
    # Start the bot
    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main() 