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

# 1. Commit and push to GitHub
echo -e "${BLUE}Committing and pushing changes to GitHub...${NC}"

# Check if there are any changes to commit
if [[ -n $(git status --porcelain) ]]; then
    # Prompt for commit message
    echo -e "${YELLOW}Enter commit message:${NC}"
    read commit_message
    
    # Add all changes
    git add .
    
    # Commit with the provided message
    git commit -m "$commit_message"
    
    # Push to GitHub
    git push origin main
    
    echo -e "${GREEN}Changes pushed to GitHub successfully!${NC}"
else
    echo -e "${YELLOW}No changes to commit. Continuing with deployment...${NC}"
fi

echo -e "${YELLOW}Deploying Indexsy Telegram Bot to remote server...${NC}"

# 2. Create the project directory on the server if it doesn't exist
echo -e "${GREEN}Creating project directory...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "mkdir -p ${REMOTE_DIR}"

# 3. Option 1: Copy all necessary files to the server
echo -e "${GREEN}Copying files to server...${NC}"
scp bot.py requirements.txt .env .env.example deploy.sh test_watchdog.py README.md indexsy-bot.service ${DROPLET_USER}@${DROPLET_IP}:${REMOTE_DIR}/

# 4. Option 2: Or clone/pull from GitHub (uncomment to use this method instead)
# echo -e "${GREEN}Updating code from GitHub...${NC}"
# ssh ${DROPLET_USER}@${DROPLET_IP} "cd ${REMOTE_DIR} && \
#     if [ -d .git ]; then \
#         git pull; \
#     else \
#         git clone ${GITHUB_REPO} .; \
#     fi && \
#     cp /root/projects/.env ${REMOTE_DIR}/.env"

# 5. Set up the systemd service
echo -e "${GREEN}Setting up systemd service...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "cp ${REMOTE_DIR}/indexsy-bot.service /etc/systemd/system/ && \
    systemctl daemon-reload && \
    systemctl enable indexsy-bot.service"

# 6. Run the deployment script on the server
echo -e "${GREEN}Running deployment script on server...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "cd ${REMOTE_DIR} && chmod +x deploy.sh && ./deploy.sh"

# 7. Start the service
echo -e "${GREEN}Starting the bot service...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "systemctl start indexsy-bot.service"

# 8. Check service status
echo -e "${GREEN}Checking service status...${NC}"
ssh ${DROPLET_USER}@${DROPLET_IP} "systemctl status indexsy-bot.service"

echo -e "${YELLOW}Deployment complete!${NC}"
echo -e "To check logs: ssh ${DROPLET_USER}@${DROPLET_IP} 'tail -f ${REMOTE_DIR}/bot.log'"
echo -e "To restart the bot: ssh ${DROPLET_USER}@${DROPLET_IP} 'systemctl restart indexsy-bot.service'" 