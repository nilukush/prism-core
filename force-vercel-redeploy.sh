#!/bin/bash

# Force Vercel Redeployment Script
# This script forces Vercel to use the latest commit by making a minimal change

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}       Force Vercel Redeployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

cd frontend || exit 1

echo -e "${YELLOW}Current git status:${NC}"
git log --oneline -1
echo ""

echo -e "${BLUE}Option 1: Force deployment by adding deployment timestamp${NC}"
echo -e "${YELLOW}This will add a comment to package.json to trigger rebuild${NC}"
echo ""

# Create a timestamp comment in package.json
TIMESTAMP=$(date +"%Y-%m-%d %H:%M:%S")
sed -i.bak '1s/^/\/\/ Deployment forced at: '"$TIMESTAMP"'\n/' package.json

echo -e "${GREEN}✅ Added deployment timestamp to package.json${NC}"
echo ""

echo -e "${BLUE}Committing change...${NC}"
git add package.json
git commit -m "Force Vercel deployment - ${TIMESTAMP}"

echo -e "${BLUE}Pushing to trigger deployment...${NC}"
git push origin HEAD:main

echo ""
echo -e "${GREEN}✅ Change pushed! Vercel should now deploy the latest code.${NC}"
echo ""
echo -e "${YELLOW}Monitor deployment at:${NC}"
echo "https://vercel.com/nilukushs-projects/prism/deployments"
echo ""
echo -e "${YELLOW}To revert the timestamp later:${NC}"
echo "git revert HEAD"