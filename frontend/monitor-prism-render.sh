#!/bin/bash

# PRISM Backend Render Monitoring Script
# Usage: ./monitor-prism-render.sh

SERVICE_NAME="prism-backend-bwfx"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}PRISM Backend Monitoring - Render${NC}"
echo "===================================="
echo ""

# Check if render CLI is installed
if ! command -v render &> /dev/null; then
    echo -e "${RED}Error: Render CLI is not installed${NC}"
    echo "Install it with: brew install render"
    exit 1
fi

# Function to check service status
check_service_status() {
    echo -e "${YELLOW}Checking service status...${NC}"
    render services show --name $SERVICE_NAME 2>/dev/null
    if [ $? -ne 0 ]; then
        echo -e "${RED}Could not find service. Make sure you're logged in: render login${NC}"
        exit 1
    fi
}

# Function to show recent deployments
show_deployments() {
    echo -e "\n${YELLOW}Recent deployments:${NC}"
    render deploys list --service-name $SERVICE_NAME --limit 5
}

# Function to tail logs
tail_logs() {
    echo -e "\n${YELLOW}Tailing logs (press Ctrl+C to stop):${NC}"
    render logs --service-name $SERVICE_NAME --tail
}

# Main menu
while true; do
    echo -e "\n${GREEN}What would you like to do?${NC}"
    echo "1. Check service status"
    echo "2. View recent deployments"
    echo "3. Tail live logs"
    echo "4. View last 100 log lines"
    echo "5. Trigger new deployment"
    echo "6. Exit"
    
    read -p "Select an option (1-6): " choice
    
    case $choice in
        1)
            check_service_status
            ;;
        2)
            show_deployments
            ;;
        3)
            tail_logs
            ;;
        4)
            echo -e "\n${YELLOW}Last 100 log lines:${NC}"
            render logs --service-name $SERVICE_NAME --lines 100
            ;;
        5)
            echo -e "\n${YELLOW}Triggering new deployment...${NC}"
            render deploys create --service-name $SERVICE_NAME
            ;;
        6)
            echo -e "${GREEN}Goodbye!${NC}"
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            ;;
    esac
done