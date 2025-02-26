# Indexsy Telegram Bot

A Telegram bot that tracks engagement in group chats, counting messages and reactions.

## Features

- Tracks messages and reactions in group chats
- Provides leaderboards for engagement
- Monthly reset of statistics with history tracking
- **Self-restart mechanism** to automatically recover from crashes or hangs

## Self-Restart Mechanism

The bot includes a watchdog mechanism that monitors its activity and automatically restarts it if it becomes unresponsive. Here's how it works:

1. The bot maintains an activity timestamp that gets updated with every interaction
2. A watchdog thread checks this timestamp every minute
3. If no activity is detected for 5 minutes, the bot assumes it's stuck and restarts itself
4. Data is saved before restarting to prevent loss

### Testing the Watchdog

You can test the self-restart mechanism using the included test script:

```bash
python test_watchdog.py
```

This script will:
1. Find the running bot process
2. Simulate a hang by sending a SIGSTOP signal
3. Wait for the watchdog to detect inactivity and restart the bot
4. Report the results

Note: The test may take up to 6 minutes to complete.

## Deployment

### Local Deployment

To deploy the bot locally:

```bash
./deploy.sh
```

### Server Deployment

Several scripts are provided for different deployment scenarios:

1. **Push to GitHub only**:
   ```bash
   ./push_to_github.sh
   ```
   This script commits and pushes your changes to GitHub.

2. **Deploy from GitHub to server**:
   ```bash
   ./github_deploy.sh
   ```
   This script deploys the latest code from GitHub to your server.

3. **Push to GitHub and deploy to server**:
   ```bash
   ./push_and_deploy.sh
   ```
   This script combines both operations - it pushes your changes to GitHub and then deploys to your server.

4. **Manual deployment with file copying**:
   ```bash
   ./remote_deploy.sh
   ```
   This script copies files directly from your local machine to the server.

The deployment scripts:
1. Update the code (either from GitHub or by direct file copy)
2. Install dependencies
3. Set up the systemd service
4. Start/restart the bot

## Monitoring

To monitor the bot:

```bash
# View logs in real-time
ssh root@159.223.192.10 'tail -f /root/projects/indexsy-telegram-bot/bot.log'

# Check service status
ssh root@159.223.192.10 'systemctl status indexsy-bot.service'

# Restart the service
ssh root@159.223.192.10 'systemctl restart indexsy-bot.service'
```

## Requirements

- Python 3.7+
- python-telegram-bot
- python-dotenv

## Configuration

Create a `.env` file with your Telegram bot token:

```
TELEGRAM_BOT_TOKEN=your_bot_token_here
``` 