#!/bin/bash

# Fix Vercel Deployment Script

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Vercel Deployment Fix${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check if Vercel CLI is installed
if ! command -v vercel &> /dev/null; then
    echo -e "${YELLOW}Installing Vercel CLI...${NC}"
    npm i -g vercel
fi

echo -e "${YELLOW}Current Status:${NC}"
echo "- Vercel is deploying old commit: 2db96be"
echo "- Latest commit is: 5405bfb"
echo "- Build commands still have 'cd frontend'"
echo ""

echo -e "${BLUE}Option 1: Deploy via CLI (Recommended)${NC}"
echo "1. Run these commands:"
echo ""
echo "   cd frontend"
echo "   vercel link  # Link to your existing project"
echo "   vercel --prod --force  # Force deploy production"
echo ""

echo -e "${BLUE}Option 2: Fix via Dashboard${NC}"
echo "1. Go to: https://vercel.com/nilukushs-projects/prism"
echo "2. Click 'Settings' → 'General'"
echo "3. Under 'Build & Development Settings':"
echo "   - Build Command: ${GREEN}npm run build${NC}"
echo "   - Install Command: ${GREEN}npm install${NC}"
echo "   - Output Directory: ${GREEN}.next${NC}"
echo "4. Save changes"
echo "5. Go to 'Deployments' tab"
echo "6. Click 'Create Deployment'"
echo "7. Use latest commit or branch"
echo ""

echo -e "${BLUE}Option 3: Complete Reset${NC}"
echo "1. Delete the project in Vercel"
echo "2. Run:"
echo "   cd frontend"
echo "   rm -rf .vercel"
echo "   vercel  # Create new deployment"
echo "3. When prompted:"
echo "   - Set up and deploy? Y"
echo "   - Link to existing? N"
echo "   - Project name: prism-frontend"
echo "   - Directory: ./ (current)"
echo ""

echo -e "${YELLOW}Quick Vercel CLI Deployment:${NC}"
read -p "Do you want to try deploying via CLI now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    cd frontend
    
    echo -e "${BLUE}Checking Vercel authentication...${NC}"
    if ! vercel whoami &> /dev/null; then
        echo -e "${YELLOW}Please login to Vercel:${NC}"
        vercel login
    fi
    
    echo -e "${BLUE}Deploying to Vercel...${NC}"
    vercel --prod --force
    
    echo -e "${GREEN}✅ Deployment initiated!${NC}"
    echo "Check your Vercel dashboard for status"
fi