#!/bin/bash

echo "🔍 Checking Backend Deployment Status"
echo "===================================="
echo ""

API_URL="https://prism-backend-bwfx.onrender.com"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check health endpoint
echo -e "${YELLOW}1. Checking backend health...${NC}"
HEALTH_RESPONSE=$(curl -s "$API_URL/health" -w "\n%{http_code}")
HTTP_CODE=$(echo "$HEALTH_RESPONSE" | tail -n1)

if [ "$HTTP_CODE" = "200" ]; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
    echo "Response: $(echo "$HEALTH_RESPONSE" | head -n-1)"
else
    echo -e "${RED}❌ Backend health check failed (HTTP $HTTP_CODE)${NC}"
fi

# Check if DELETE endpoint exists
echo -e "\n${YELLOW}2. Checking DELETE endpoint availability...${NC}"

# Try OPTIONS request to see allowed methods
OPTIONS_RESPONSE=$(curl -s -X OPTIONS "$API_URL/api/v1/organizations/1/" -I 2>&1 | head -20)
echo "OPTIONS Response:"
echo "$OPTIONS_RESPONSE"

# Try actual DELETE (will fail without auth but shows if endpoint exists)
echo -e "\n${YELLOW}3. Testing DELETE endpoint (without auth)...${NC}"
DELETE_TEST=$(curl -s -X DELETE "$API_URL/api/v1/organizations/1/" -w "\n%{http_code}")
DELETE_CODE=$(echo "$DELETE_TEST" | tail -n1)

if [ "$DELETE_CODE" = "401" ] || [ "$DELETE_CODE" = "403" ]; then
    echo -e "${GREEN}✅ DELETE endpoint exists (returned auth error as expected)${NC}"
elif [ "$DELETE_CODE" = "404" ]; then
    echo -e "${RED}❌ DELETE endpoint NOT FOUND - backend needs deployment${NC}"
    echo ""
    echo "The DELETE endpoint hasn't been deployed yet. Options:"
    echo "1. Wait for Render to deploy (can take 10-15 minutes)"
    echo "2. Manually trigger deployment in Render dashboard"
    echo "3. Use SQL deletion method"
else
    echo -e "${YELLOW}⚠️  Unexpected response: HTTP $DELETE_CODE${NC}"
fi

echo -e "\n${YELLOW}4. Deployment timeline:${NC}"
echo "- Code pushed to GitHub at: ~11:47 UTC"
echo "- Expected deployment time: ~11:57-12:02 UTC"
echo "- Current time: $(date -u '+%Y-%m-%d %H:%M:%S UTC')"

MINUTES_SINCE_PUSH=$(( ($(date +%s) - $(date -d "2025-01-18 11:47:00" +%s)) / 60 ))
echo "- Minutes since push: $MINUTES_SINCE_PUSH"

if [ $MINUTES_SINCE_PUSH -lt 15 ]; then
    echo -e "${YELLOW}⏳ Backend might still be deploying. Wait a few more minutes.${NC}"
else
    echo -e "${GREEN}✅ Sufficient time has passed. Backend should be deployed.${NC}"
fi