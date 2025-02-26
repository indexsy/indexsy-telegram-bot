#!/bin/bash

# Go to project directory
cd /root/projects/indexsy-telegram-bot

# Pull latest changes from GitHub
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update requirements
pip install -r requirements.txt

# Kill ALL existing bot processes
pkill -9 -f "python bot.py" || true

# Clean up existing screen sessions
screen -X -S bot quit || true

# Remove PID file if it exists
rm -f bot.pid

# Start bot in background with screen
# Using screen allows us to reconnect to the bot process if needed
screen -S bot -dm bash -c "python bot.py >> bot.log 2>&1"

# Wait a moment for the bot to start
sleep 2

# Show last 20 lines of logs
tail -n 20 bot.log

echo "Bot deployed with self-restart capability"
echo "To view logs in real-time: screen -r bot"
echo "To detach from screen: Ctrl+A followed by D" 