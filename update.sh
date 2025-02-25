#!/bin/bash
cd /root/projects/indexsy-telegram-bot
git pull origin main

# Activate virtual environment
source venv/bin/activate

# Install requirements
pip install -r requirements.txt

# Kill existing bot process
pkill -f "python bot.py"

# Start bot in background
nohup python bot.py > bot.log 2>&1 & 