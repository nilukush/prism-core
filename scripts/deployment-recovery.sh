#!/bin/bash

# PRISM Deployment Recovery Script

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}     PRISM Deployment Recovery Assistant${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

# Issue 1: Check Render Backend
echo -e "${YELLOW}1. Checking Render Backend Status...${NC}"
echo "URL: https://prism-backend-bwfx.onrender.com"
echo ""

STATUS=$(curl -s -o /dev/null -w "%{http_code}" https://prism-backend-bwfx.onrender.com/health --max-time 10 2>/dev/null || echo "000")

if [ "$STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend is LIVE!${NC}"
else
    echo -e "${RED}❌ Backend not responding (Status: $STATUS)${NC}"
    echo ""
    echo -e "${YELLOW}Common Render Issues:${NC}"
    echo "1. Missing PORT environment variable (must be 8000)"
    echo "2. Build failed - check logs in Render dashboard"
    echo "3. Service sleeping (free tier) - may need manual restart"
    echo ""
    echo -e "${BLUE}To fix:${NC}"
    echo "1. Go to Render Dashboard → prism-backend-bwfx"
    echo "2. Check 'Logs' tab for errors"
    echo "3. Verify these critical env vars exist:"
    echo "   - PORT=8000"
    echo "   - DATABASE_URL (your Neon URL)"
    echo "   - UPSTASH_REDIS_REST_URL"
    echo "   - SECRET_KEY"
    echo "4. Try 'Manual Deploy' → 'Clear build cache & deploy'"
fi

echo ""
echo -e "${YELLOW}2. OpenAI API Key Status...${NC}"

# Test if we can use the API key locally
if [ -f ".env.production" ]; then
    source .env.production 2>/dev/null || true
    if [ ! -z "$OPENAI_API_KEY" ]; then
        echo -e "${YELLOW}Testing API key locally...${NC}"
        
        # Create test script
        cat > test_openai.py << 'EOF'
import os
import sys
try:
    from openai import OpenAI
    client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
    # Just test the key is valid
    models = client.models.list()
    print("✅ API key is valid!")
except Exception as e:
    if "401" in str(e) or "Incorrect API key" in str(e):
        print("❌ API key is invalid or expired")
        print("   Generate a new key at: https://platform.openai.com/api-keys")
    else:
        print(f"❌ Error: {str(e)}")
    sys.exit(1)
EOF
        
        python test_openai.py 2>/dev/null || echo -e "${RED}API key test failed${NC}"
        rm -f test_openai.py
    else
        echo -e "${RED}No API key found in .env.production${NC}"
    fi
else
    echo -e "${YELLOW}No .env.production file found${NC}"
fi

echo ""
echo -e "${BLUE}To get a new OpenAI API key:${NC}"
echo "1. Go to https://platform.openai.com/api-keys"
echo "2. Click 'Create new secret key'"
echo "3. Copy the key (starts with sk-...)"
echo "4. Add to Render environment variables:"
echo "   OPENAI_API_KEY=sk-..."
echo ""

# Issue 3: Vercel Frontend
echo -e "${YELLOW}3. Fixing Vercel Deployment...${NC}"
echo ""

# Check if frontend directory exists
if [ -d "frontend" ]; then
    echo -e "${GREEN}✅ Frontend directory exists${NC}"
    
    # Create vercel.json if it doesn't exist
    if [ ! -f "frontend/vercel.json" ]; then
        echo -e "${YELLOW}Creating vercel.json...${NC}"
        cat > frontend/vercel.json << EOF
{
  "buildCommand": "npm run build",
  "outputDirectory": ".next",
  "devCommand": "npm run dev",
  "installCommand": "npm install",
  "framework": "nextjs",
  "env": {
    "NEXT_PUBLIC_API_URL": "https://prism-backend-bwfx.onrender.com"
  }
}
EOF
        echo -e "${GREEN}✅ Created frontend/vercel.json${NC}"
    fi
    
    # Create .env.production for frontend
    cat > frontend/.env.production << EOF
NEXT_PUBLIC_API_URL=https://prism-backend-bwfx.onrender.com
NEXTAUTH_URL=https://your-app.vercel.app
NEXTAUTH_SECRET=$(openssl rand -base64 32)
EOF
    echo -e "${GREEN}✅ Created frontend/.env.production${NC}"
    
else
    echo -e "${RED}❌ Frontend directory not found!${NC}"
    echo "Your frontend might be in a different location"
fi

echo ""
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}            Deployment Steps${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

echo -e "${YELLOW}Step 1: Fix Render Backend${NC}"
echo "1. Check Render logs for specific errors"
echo "2. Ensure all environment variables are set:"
cat << 'EOF'
   PORT=8000
   DATABASE_URL=postgresql://...
   UPSTASH_REDIS_REST_URL=https://...
   UPSTASH_REDIS_REST_TOKEN=...
   SECRET_KEY=...
   JWT_SECRET_KEY=...
   DEFAULT_LLM_PROVIDER=openai
   DEFAULT_LLM_MODEL=gpt-3.5-turbo
   OPENAI_API_KEY=sk-proj-...
   AI_CACHE_ENABLED=true
   AI_MONTHLY_BUDGET_USD=20
EOF
echo "3. Try 'Clear build cache & deploy' in Render"
echo ""

echo -e "${YELLOW}Step 2: Update OpenAI API Key${NC}"
echo "1. Generate new key at https://platform.openai.com/api-keys"
echo "2. Update in Render environment variables"
echo "3. Restart the service"
echo ""

echo -e "${YELLOW}Step 3: Deploy Frontend to Vercel${NC}"
echo "Option A - Via Vercel Dashboard:"
echo "1. Import project from GitHub"
echo "2. Set Root Directory to 'frontend'"
echo "3. Add environment variable:"
echo "   NEXT_PUBLIC_API_URL = https://prism-backend-bwfx.onrender.com"
echo ""
echo "Option B - Via CLI:"
echo "cd frontend"
echo "vercel --prod"
echo ""

echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo -e "${GREEN}         Quick Test Commands${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════${NC}"
echo ""
echo "# Test backend health"
echo "curl https://prism-backend-bwfx.onrender.com/health"
echo ""
echo "# View API docs (once live)"
echo "open https://prism-backend-bwfx.onrender.com/docs"
echo ""
echo "# Test OpenAI integration (once live)"
echo "curl -X POST https://prism-backend-bwfx.onrender.com/api/v1/ai/config/test \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"test\": true}'"
echo ""

echo -e "${BLUE}Need more help? Check:${NC}"
echo "- Render logs: https://dashboard.render.com"
echo "- Full guide: RENDER_DEPLOYMENT_CHECKLIST.md"
echo "- Status: ./scripts/check-render-status.sh"