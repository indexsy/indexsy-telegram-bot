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

# Start bot in background
screen -S bot -dm python bot.py

# Wait a moment for the bot to start
sleep 2

# Show last 20 lines of logs
tail -n 20 bot.log 