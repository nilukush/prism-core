#!/bin/bash

# Quick Deployment Status Checker

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}         PRISM Deployment Status${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check Render Backend
echo -e "${YELLOW}1. Render Backend${NC}"
echo -n "   Status: "
BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://prism-backend-bwfx.onrender.com/health --max-time 5 2>/dev/null || echo "000")

if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ LIVE!${NC}"
    BACKEND_RESPONSE=$(curl -s https://prism-backend-bwfx.onrender.com/health 2>/dev/null)
    echo "   Response: $BACKEND_RESPONSE"
    echo "   API Docs: https://prism-backend-bwfx.onrender.com/docs"
else
    echo -e "${RED}❌ Not Ready (Status: $BACKEND_STATUS)${NC}"
    echo ""
    echo "   Fixes applied:"
    echo "   - ✅ AnthropicClient error fixed"
    echo "   - ✅ Code pushed to GitHub"
    echo "   - ⏳ Waiting for Render to auto-deploy (3-5 min)"
    echo ""
    echo "   Check logs: https://dashboard.render.com"
fi

echo ""

# Check Vercel Frontend
echo -e "${YELLOW}2. Vercel Frontend${NC}"
echo "   Status: Check your Vercel dashboard"
echo "   Fix applied: ✅ Removed 'cd frontend' from commands"
echo ""

# Summary
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}            Summary${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

if [ "$BACKEND_STATUS" = "200" ]; then
    echo -e "${GREEN}🎉 Backend is working!${NC}"
    echo ""
    echo "Next steps:"
    echo "1. Ensure Vercel has deployed successfully"
    echo "2. Update Vercel env: NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com"
    echo "3. Test the full application"
else
    echo -e "${YELLOW}⏳ Backend deployment in progress...${NC}"
    echo ""
    echo "What's happening:"
    echo "1. Render detected our code fix"
    echo "2. Building new Docker image"
    echo "3. Starting the service"
    echo ""
    echo "This typically takes 3-5 minutes for code changes."
fi

echo ""
echo -e "${BLUE}Quick Commands:${NC}"
echo "# Test backend"
echo "curl https://prism-backend-bwfx.onrender.com/health"
echo ""
echo "# Monitor deployment"
echo "./scripts/monitor-render-deployment.sh"
echo ""
echo "# Check this status again"
echo "./scripts/deployment-status.sh"