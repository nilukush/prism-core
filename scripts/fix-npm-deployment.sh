#!/bin/bash

# Fix NPM Deployment Issues

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}═══════════════════════════════════════════════${NC}"
echo -e "${RED}    NPM Package Installation Fix${NC}"
echo -e "${RED}═══════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Issue: @radix-ui/react-badge 404 error${NC}"
echo "The npm registry URL is getting encoded incorrectly"
echo ""

cd frontend

echo -e "${BLUE}Step 1: Clean npm cache${NC}"
npm cache clean --force

echo -e "${BLUE}Step 2: Remove existing lock file${NC}"
rm -f package-lock.json

echo -e "${BLUE}Step 3: Set npm registry explicitly${NC}"
npm config set registry https://registry.npmjs.org/

echo -e "${BLUE}Step 4: Fresh install with correct registry${NC}"
npm install

echo -e "${BLUE}Step 5: Verify @radix-ui/react-badge installed${NC}"
npm list @radix-ui/react-badge

echo -e "${BLUE}Step 6: Commit the new package-lock.json${NC}"
cd ..
git add frontend/package-lock.json
git commit -m "Fix: Regenerate package-lock.json to fix npm 404 errors

- Fixed @radix-ui/react-badge installation issue
- Removed corrupted package-lock.json
- Fresh install with correct npm registry
- Fixes Vercel deployment npm errors"

echo -e "${GREEN}✅ Fix complete!${NC}"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Push to GitHub: git push"
echo "2. Redeploy in Vercel dashboard"
echo "3. Or use: cd frontend && vercel --prod --force"