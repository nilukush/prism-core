#!/bin/bash

# Monitor Render Deployment Progress

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo -e "${BLUE}    Monitoring Render Deployment${NC}"
echo -e "${BLUE}═══════════════════════════════════════════════${NC}"
echo ""

URL="https://prism-backend-bwfx.onrender.com/health"
CHECK_INTERVAL=15
MAX_ATTEMPTS=40  # 10 minutes total

echo "URL: $URL"
echo "Checking every $CHECK_INTERVAL seconds..."
echo ""

attempt=1
while [ $attempt -le $MAX_ATTEMPTS ]; do
    echo -n "[$attempt/$MAX_ATTEMPTS] $(date '+%H:%M:%S') - "
    
    # Check status
    STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$URL" --max-time 10 2>/dev/null || echo "000")
    
    case $STATUS in
        200)
            echo -e "${GREEN}✅ BACKEND IS LIVE!${NC}"
            echo ""
            
            # Get full response
            RESPONSE=$(curl -s "$URL" 2>/dev/null)
            echo "Response: $RESPONSE"
            echo ""
            
            echo -e "${GREEN}🎉 Deployment Successful!${NC}"
            echo ""
            echo "Next steps:"
            echo "1. API Docs: https://prism-backend-bwfx.onrender.com/docs"
            echo "2. Fix Vercel by removing 'cd frontend' from commands"
            echo "3. Your app will be fully deployed!"
            
            # Show quick test
            echo ""
            echo -e "${BLUE}Quick API Test:${NC}"
            curl -s https://prism-backend-bwfx.onrender.com/api/v1/ | jq . 2>/dev/null || echo "API root endpoint"
            
            exit 0
            ;;
            
        000)
            echo -e "${YELLOW}⏳ No response (timeout/connection refused)${NC}"
            ;;
            
        502|503|504)
            echo -e "${YELLOW}⏳ Service starting up (Status: $STATUS)${NC}"
            ;;
            
        404)
            echo -e "${RED}❌ 404 Not Found - Check if URL is correct${NC}"
            ;;
            
        500)
            echo -e "${RED}❌ 500 Internal Server Error - Check logs!${NC}"
            echo ""
            echo "Likely issues:"
            echo "1. Missing PORT=8000 environment variable"
            echo "2. Database connection error"
            echo "3. Missing required environment variables"
            echo ""
            echo "Check logs at: https://dashboard.render.com"
            ;;
            
        *)
            echo -e "${YELLOW}⚠️  Unexpected status: $STATUS${NC}"
            ;;
    esac
    
    # Show progress bar
    if [ $attempt -lt $MAX_ATTEMPTS ]; then
        echo -n "Progress: ["
        for i in $(seq 1 40); do
            if [ $i -le $((attempt * 40 / MAX_ATTEMPTS)) ]; then
                echo -n "="
            else
                echo -n " "
            fi
        done
        echo "] $((attempt * 100 / MAX_ATTEMPTS))%"
    fi
    
    attempt=$((attempt + 1))
    
    if [ $attempt -le $MAX_ATTEMPTS ]; then
        sleep $CHECK_INTERVAL
    fi
done

echo ""
echo -e "${RED}❌ Deployment timed out after 10 minutes${NC}"
echo ""
echo "Troubleshooting steps:"
echo "1. Check Render logs: https://dashboard.render.com"
echo "2. Look for build errors or missing environment variables"
echo "3. Common fix: Add PORT=8000 to environment variables"
echo "4. Try: Manual Deploy → Clear build cache & deploy"
echo ""
echo "Most common issues:"
echo "- Missing PORT=8000 environment variable"
echo "- Database URL format (our code fix should handle this)"
echo "- Build failed due to dependency issues"