#!/bin/bash

# Kill any existing bot processes
pkill -f "python bot.py" || true

# Remove PID file if it exists
rm -f bot.pid

# Activate virtual environment
source venv/bin/activate

# Run the bot
python bot.py 