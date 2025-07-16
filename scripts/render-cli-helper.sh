#!/bin/bash

# Render CLI Helper Script for PRISM

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}          Render CLI Helper for PRISM${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check if Render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${YELLOW}Render CLI not found. Installing...${NC}"
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        if command -v brew &> /dev/null; then
            brew update && brew install render
        else
            curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
        fi
    else
        # Linux
        curl -fsSL https://raw.githubusercontent.com/render-oss/cli/refs/heads/main/bin/install.sh | sh
    fi
    
    echo -e "${GREEN}✅ Render CLI installed${NC}"
fi

# Check if logged in
if ! render whoami &> /dev/null; then
    echo -e "${YELLOW}Not logged in to Render. Please login:${NC}"
    render login
fi

# Function to get service ID
get_service_id() {
    echo -e "${BLUE}Fetching your services...${NC}"
    render services --output json | jq -r '.[] | select(.name | contains("prism")) | "\(.id) - \(.name) (\(.type))"'
    
    echo ""
    read -p "Enter your service ID (or partial name): " SERVICE_INPUT
    
    # Try to find the service
    SERVICE_ID=$(render services --output json | jq -r ".[] | select(.name | contains(\"$SERVICE_INPUT\") or .id | contains(\"$SERVICE_INPUT\")) | .id" | head -1)
    
    if [ -z "$SERVICE_ID" ]; then
        echo -e "${RED}Service not found${NC}"
        exit 1
    fi
    
    echo -e "${GREEN}Using service: $SERVICE_ID${NC}"
}

# Main menu
while true; do
    echo ""
    echo -e "${BLUE}What would you like to do?${NC}"
    echo "1) View deployment logs"
    echo "2) Check service status"
    echo "3) Restart service"
    echo "4) Fix database URL (add asyncpg)"
    echo "5) List recent deploys"
    echo "6) SSH into service"
    echo "7) Exit"
    echo ""
    read -p "Enter your choice (1-7): " choice
    
    case $choice in
        1)
            get_service_id
            echo -e "${BLUE}Tailing logs for $SERVICE_ID...${NC}"
            echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
            render logs "$SERVICE_ID"
            ;;
            
        2)
            get_service_id
            echo -e "${BLUE}Service Status:${NC}"
            render services --output json | jq ".[] | select(.id == \"$SERVICE_ID\")"
            ;;
            
        3)
            get_service_id
            echo -e "${YELLOW}Restarting service...${NC}"
            render restart "$SERVICE_ID" --confirm
            echo -e "${GREEN}✅ Restart initiated${NC}"
            ;;
            
        4)
            echo -e "${YELLOW}To fix the database URL:${NC}"
            echo "1. Go to https://dashboard.render.com"
            echo "2. Click on your service: prism-backend-bwfx"
            echo "3. Go to 'Environment' tab"
            echo "4. Find DATABASE_URL"
            echo "5. Change:"
            echo "   FROM: postgresql://neondb_owner:..."
            echo "   TO:   postgresql+asyncpg://neondb_owner:..."
            echo "6. Click 'Save Changes'"
            echo ""
            echo -e "${BLUE}The service will automatically redeploy with the fix${NC}"
            ;;
            
        5)
            get_service_id
            echo -e "${BLUE}Recent deploys:${NC}"
            render deploys list "$SERVICE_ID" --limit 5
            ;;
            
        6)
            get_service_id
            echo -e "${BLUE}Opening SSH session...${NC}"
            render ssh "$SERVICE_ID"
            ;;
            
        7)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
            
        *)
            echo -e "${RED}Invalid choice${NC}"
            ;;
    esac
done