#!/bin/bash

# Go to project directory
cd /root/projects/indexsy-telegram-bot

# Pull latest changes from GitHub
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install/update requirementsd
pip install -r requirements.txt

# Kill existing bot process
pkill -f "python bot.py"

# Start bot in background
screen -S bot -dm python bot.py

# Show logs
tail -f bot.log 