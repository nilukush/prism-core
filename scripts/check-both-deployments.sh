#!/bin/bash

# Check Both Deployments Status

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

clear

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}    PRISM Full Deployment Status Check${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Check Render Backend
echo -e "${YELLOW}1. RENDER BACKEND${NC}"
echo "   URL: https://prism-backend-bwfx.onrender.com"
echo -n "   Status: "

BACKEND_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://prism-backend-bwfx.onrender.com/health --max-time 10 2>/dev/null || echo "timeout")

case $BACKEND_STATUS in
    200)
        echo -e "${GREEN}✅ LIVE!${NC}"
        RESPONSE=$(curl -s https://prism-backend-bwfx.onrender.com/health 2>/dev/null)
        echo "   Response: $RESPONSE"
        echo -e "   ${GREEN}Backend is working!${NC}"
        ;;
    timeout)
        echo -e "${RED}❌ Timeout (service not responding)${NC}"
        echo ""
        echo "   Last fix applied: AnthropicClient error"
        echo "   Deployment should complete in 3-5 minutes"
        echo "   Check logs: https://dashboard.render.com"
        ;;
    502|503)
        echo -e "${YELLOW}⏳ Starting up (Status: $BACKEND_STATUS)${NC}"
        ;;
    *)
        echo -e "${RED}❌ Error (Status: $BACKEND_STATUS)${NC}"
        ;;
esac

echo ""

# Check Vercel Frontend
echo -e "${YELLOW}2. VERCEL FRONTEND${NC}"
echo "   ${RED}❌ DEPLOYMENT FAILING${NC}"
echo ""
echo "   Error: ${RED}cd: frontend: No such file or directory${NC}"
echo ""
echo -e "   ${YELLOW}REQUIRED FIX:${NC}"
echo "   1. Go to Vercel project settings"
echo "   2. Build & Development Settings"
echo "   3. UPDATE these commands:"
echo ""
echo "      Build Command: ${GREEN}npm run build${NC} (remove 'cd frontend &&')"
echo "      Install Command: ${GREEN}npm install${NC} (remove 'cd frontend &&')"
echo "      Output Directory: ${GREEN}.next${NC}"
echo ""
echo "   4. Clear build cache"
echo "   5. Redeploy"

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}            ACTION ITEMS${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

if [ "$BACKEND_STATUS" != "200" ]; then
    echo "1. ${YELLOW}RENDER${NC}: Wait for deployment (3-5 min)"
    echo "   - Our fix for AnthropicClient was pushed"
    echo "   - Should auto-deploy and start working"
else
    echo "1. ${GREEN}RENDER${NC}: ✅ Backend is working!"
fi

echo ""
echo "2. ${RED}VERCEL${NC}: NEEDS IMMEDIATE FIX"
echo "   - Remove 'cd frontend' from ALL commands"
echo "   - Clear cache and redeploy"
echo "   - Make sure using latest commit (4868d4c)"
echo ""

# Show git info
echo -e "${BLUE}Git Information:${NC}"
CURRENT_COMMIT=$(git rev-parse --short HEAD 2>/dev/null || echo "unknown")
echo "   Current local commit: $CURRENT_COMMIT"
echo "   Vercel is deploying: 2db96be (OLD!)"
echo "   Latest commit: 4868d4c"
echo ""

echo -e "${BLUE}Quick Commands:${NC}"
echo "# Test backend when ready"
echo "curl https://prism-backend-bwfx.onrender.com/health"
echo ""
echo "# Force push to update Vercel"
echo "git push origin main --force-with-lease"
echo ""
echo "# Check status again"
echo "./scripts/check-both-deployments.sh"