#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}   PUSH TO GITHUB AND DEPLOY TO SERVER  ${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 1: Push to GitHub
echo -e "\n${YELLOW}STEP 1: Pushing changes to GitHub...${NC}"

# Check if there are any changes to commit
if [[ -n $(git status --porcelain) ]]; then
    # Prompt for commit message
    echo -e "${YELLOW}Enter commit message:${NC}"
    read commit_message
    
    if [[ -z "$commit_message" ]]; then
        echo -e "${RED}Commit message cannot be empty. Aborting.${NC}"
        exit 1
    fi
    
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

# Step 2: Deploy to server
echo -e "\n${YELLOW}STEP 2: Deploying to server...${NC}"
echo -e "${YELLOW}Do you want to deploy to the server? (y/n)${NC}"
read deploy_answer

if [[ "$deploy_answer" == "y" || "$deploy_answer" == "Y" ]]; then
    # Run the GitHub deployment script
    ./github_deploy.sh
else
    echo -e "${YELLOW}Deployment skipped.${NC}"
fi

echo -e "\n${GREEN}All operations completed!${NC}" 