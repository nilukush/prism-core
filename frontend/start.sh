#!/bin/bash

# PRISM Frontend Startup Script
# Enterprise-grade startup with health checks and error handling

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${YELLOW}Starting PRISM Frontend...${NC}"

# Check if node_modules exists
if [ ! -d "node_modules" ]; then
    echo -e "${YELLOW}Installing dependencies...${NC}"
    npm install
fi

# Check if .next build directory exists
if [ ! -d ".next" ] && [ "$1" != "dev" ]; then
    echo -e "${YELLOW}Building application...${NC}"
    npm run build
fi

# Set environment variables
export NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL:-http://localhost:8100}
export NEXT_PUBLIC_APP_URL=${NEXT_PUBLIC_APP_URL:-http://localhost:3100}
export PORT=${PORT:-3100}

# Check if backend is running
echo -n "Checking backend connectivity... "
if curl -s -o /dev/null -w "%{http_code}" "$NEXT_PUBLIC_API_URL/health" | grep -q "200"; then
    echo -e "${GREEN}✓ Backend is running${NC}"
else
    echo -e "${RED}✗ Backend is not accessible at $NEXT_PUBLIC_API_URL${NC}"
    echo -e "${YELLOW}Make sure backend is running: docker compose up -d backend${NC}"
fi

# Start based on mode
if [ "$1" = "dev" ]; then
    echo -e "${GREEN}Starting in DEVELOPMENT mode on port $PORT...${NC}"
    npm run dev
elif [ "$1" = "prod" ]; then
    echo -e "${GREEN}Starting in PRODUCTION mode on port $PORT...${NC}"
    npm start
else
    echo -e "${GREEN}Starting in DEVELOPMENT mode on port $PORT...${NC}"
    echo -e "${YELLOW}Tip: Use './start.sh prod' for production mode${NC}"
    npm run dev
fi