#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${YELLOW}Pushing changes to GitHub...${NC}"

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
    echo -e "${YELLOW}No changes to commit.${NC}"
fi 