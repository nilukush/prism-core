#!/bin/bash

# Monitor Vercel Deployment

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Vercel Deployment Monitor${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Installing Vercel CLI...${NC}"
    npm i -g vercel
fi

echo -e "${YELLOW}Checking Vercel deployment status...${NC}"
echo ""

# Get deployment info
echo -e "${BLUE}Recent Deployments:${NC}"
cd frontend
vercel list --limit 3

echo ""
echo -e "${BLUE}To view logs of a specific deployment:${NC}"
echo "vercel logs [deployment-url]"
echo ""
echo "Example: vercel logs prism-ten.vercel.app"

echo ""
echo -e "${YELLOW}Quick Status Check:${NC}"
echo "1. Check if build succeeded"
echo "2. Look for 'Ready' status"
echo "3. Visit the deployment URL"

echo ""
echo -e "${BLUE}If deployment failed:${NC}"
echo "- Check if it says 'npm install --legacy-peer-deps --force' in the logs"
echo "- Look for any new errors"
echo "- Try alternative commands if needed"

echo ""
echo -e "${GREEN}Alternative Install Commands:${NC}"
echo "1. yarn install"
echo "2. npx pnpm install"
echo "3. npm ci --force"