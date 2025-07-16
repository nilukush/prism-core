#!/bin/bash

# Quick Fix Script for Current Deployment Issues

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${RED}═══════════════════════════════════════════════${NC}"
echo -e "${RED}    🚨 QUICK FIX FOR DEPLOYMENT ISSUES 🚨${NC}"
echo -e "${RED}═══════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Issue #1: Render Backend - psycopg2 Error${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "The error in your logs:"
echo -e "${RED}ModuleNotFoundError: No module named 'psycopg2'${NC}"
echo ""
echo -e "${GREEN}SOLUTION:${NC}"
echo "1. Go to: https://dashboard.render.com"
echo "2. Click on: prism-backend-bwfx"
echo "3. Go to: Environment tab"
echo "4. Find: DATABASE_URL"
echo "5. Change from:"
echo -e "${RED}postgresql://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require${NC}"
echo ""
echo "6. Change to:"
echo -e "${GREEN}postgresql+asyncpg://neondb_owner:npg_rQk92nifVozE@ep-tiny-grass-aet08v5u-pooler.c-2.us-east-2.aws.neon.tech/neondb?sslmode=require${NC}"
echo ""
echo "7. Click 'Save Changes' - Service will auto-restart"
echo ""
echo -e "${YELLOW}Press Enter when you've made this change...${NC}"
read

echo ""
echo -e "${YELLOW}Issue #2: Vercel Frontend Build${NC}"
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo "The error in your logs:"
echo -e "${RED}sh: line 1: cd: frontend: No such file or directory${NC}"
echo ""
echo -e "${GREEN}SOLUTION:${NC}"
echo "1. Go to your Vercel project settings"
echo "2. Under 'Build & Development Settings':"
echo "   - Build Command: npm run build"
echo "   - Output Directory: .next"
echo "   - Install Command: npm install"
echo "3. Make sure NO commands have 'cd frontend' in them"
echo "4. Save and redeploy"
echo ""
echo -e "${YELLOW}Press Enter when you've made this change...${NC}"
read

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Let's Test Your Fixes!${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Test Render backend
echo -n "Testing Render backend... "
RENDER_STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://prism-backend-bwfx.onrender.com/health --max-time 10 2>/dev/null || echo "000")

if [ "$RENDER_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ WORKING!${NC}"
    
    # Get the response
    RESPONSE=$(curl -s https://prism-backend-bwfx.onrender.com/health)
    echo "Response: $RESPONSE"
    
    echo ""
    echo -e "${GREEN}🎉 Your backend is now live!${NC}"
    echo "API Docs: https://prism-backend-bwfx.onrender.com/docs"
else
    echo -e "${RED}❌ Still not working (Status: $RENDER_STATUS)${NC}"
    echo ""
    echo "Possible reasons:"
    echo "1. Service is still restarting (wait 2-3 minutes)"
    echo "2. DATABASE_URL wasn't updated correctly"
    echo "3. There's another error in the logs"
    echo ""
    echo "Check logs at: https://dashboard.render.com → prism-backend-bwfx → Logs"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}         Next Steps${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

if [ "$RENDER_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend is working!${NC}"
    echo ""
    echo "1. Your Vercel frontend should deploy successfully now"
    echo "2. Update these in Vercel environment variables:"
    echo "   NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com"
    echo ""
    echo "3. Test the full application flow"
else
    echo -e "${YELLOW}⏳ Backend still starting up${NC}"
    echo ""
    echo "1. Wait 2-3 minutes and run this script again"
    echo "2. If still failing, check Render logs for new errors"
    echo "3. Make sure you added '+asyncpg' to the DATABASE_URL"
fi

echo ""
echo -e "${BLUE}Monitoring Commands:${NC}"
echo "# Check backend status"
echo "curl https://prism-backend-bwfx.onrender.com/health"
echo ""
echo "# View API documentation"
echo "open https://prism-backend-bwfx.onrender.com/docs"
echo ""
echo "# Test AI configuration"
echo "curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/ai/config/test \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"test\": true}'"