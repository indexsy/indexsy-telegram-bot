#!/bin/bash

# Server details
DROPLET_IP="159.223.192.10"
DROPLET_USER="root"
REMOTE_DIR="/root/projects/indexsy-telegram-bot"
GITHUB_REPO="https://github.com/indexsy/indexsy-telegram-bot.git"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Deploying Indexsy Telegram Bot from GitHub to remote server...${NC}"

# 1. Create the project directory on the server if it doesn't exist
echo -e "${GREEN}Creating project directory...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "mkdir -p ${REMOTE_DIR}"

# 2. Clone or pull from GitHub
echo -e "${GREEN}Updating code from GitHub...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ${REMOTE_DIR} && \
    if [ -d .git ]; then \
        git pull; \
    else \
        git clone ${GITHUB_REPO} .; \
    fi"

# 3. Copy the .env file if it exists on the server but not in the repo
echo -e "${GREEN}Checking for .env file...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "if [ ! -f ${REMOTE_DIR}/.env ] && [ -f /root/projects/.env ]; then \
    cp /root/projects/.env ${REMOTE_DIR}/.env; \
    echo 'Copied existing .env file'; \
fi"

# 4. Set up the systemd service
echo -e "${GREEN}Setting up systemd service...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "cp ${REMOTE_DIR}/indexsy-bot.service /etc/systemd/system/ && \
    systemctl daemon-reload && \
    systemctl enable indexsy-bot.service"

# 5. Set up virtual environment if it doesn't exist
echo -e "${GREEN}Setting up virtual environment...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ${REMOTE_DIR} && \
    if [ ! -d venv ]; then \
        python3 -m venv venv; \
    fi && \
    source venv/bin/activate && \
    pip install -r requirements.txt"

# 6. Start the service
echo -e "${GREEN}Starting the bot service...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "systemctl restart indexsy-bot.service"

# 7. Check service status
echo -e "${GREEN}Checking service status...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "systemctl status indexsy-bot.service"

echo -e "${YELLOW}Deployment complete!${NC}"
echo -e "To check logs: ssh ${DROPLET_USER}@${DROPLET_IP} 'tail -f ${REMOTE_DIR}/bot.log'"
echo -e "To restart the bot: ssh ${DROPLET_USER}@${DROPLET_IP} 'systemctl restart indexsy-bot.service'" 