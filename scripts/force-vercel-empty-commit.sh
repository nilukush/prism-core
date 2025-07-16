#!/bin/bash

# Force Vercel deployment with empty commit

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Force Vercel Deployment (Empty Commit)${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

cd frontend || exit 1

echo -e "${YELLOW}Current commit:${NC}"
git log --oneline -1
echo ""

echo -e "${BLUE}Creating empty commit to trigger deployment...${NC}"
git commit --allow-empty -m "Force Vercel deployment - trigger build with latest code"

echo -e "${BLUE}Pushing to main branch...${NC}"
git push origin main

echo ""
echo -e "${GREEN}✅ Empty commit pushed!${NC}"
echo ""
echo -e "${YELLOW}This should trigger Vercel to deploy with the latest code.${NC}"
echo -e "${YELLOW}Check deployment status at:${NC}"
echo "https://vercel.com/nilukushs-projects/prism/deployments"
echo ""
echo -e "${BLUE}The deployment should use commit 0279ba9 (or newer).${NC}"
echo -e "${BLUE}If it still uses 5405bfb, try Option 1 from trigger-vercel-deployment.md${NC}"