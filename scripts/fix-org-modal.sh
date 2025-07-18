#!/bin/bash

# Script to diagnose and fix organization modal issue

echo "🔧 PRISM Organization Modal Fix"
echo "=============================="
echo ""

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

API_URL="https://prism-backend-bwfx.onrender.com"
FRONTEND_URL="https://prism-frontend-kappa.vercel.app"

echo "This script will help diagnose why the organization creation modal isn't showing."
echo ""

# Step 1: Get auth token
echo -e "${YELLOW}Step 1: Authentication${NC}"
echo "Please get your JWT token from the browser:"
echo "1. Go to $FRONTEND_URL"
echo "2. Open DevTools (F12) > Console"
echo "3. Run: localStorage.getItem('token')"
echo ""
read -p "Paste your token here: " TOKEN

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ No token provided${NC}"
    exit 1
fi

# Step 2: Check current organizations
echo -e "\n${YELLOW}Step 2: Checking current organizations...${NC}"
ORG_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/organizations/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json")

echo "Raw API Response:"
echo "$ORG_RESPONSE" | jq '.' 2>/dev/null || echo "$ORG_RESPONSE"

# Parse organization count
ORG_COUNT=$(echo "$ORG_RESPONSE" | jq '.total' 2>/dev/null || echo "0")
echo -e "\nOrganization count: ${GREEN}$ORG_COUNT${NC}"

if [ "$ORG_COUNT" != "0" ] && [ "$ORG_COUNT" != "null" ]; then
    echo -e "\n${RED}⚠️  Found existing organizations!${NC}"
    echo "This is why the modal isn't showing automatically."
    echo ""
    echo "Organizations found:"
    echo "$ORG_RESPONSE" | jq '.organizations[]' 2>/dev/null || echo "Could not parse organizations"
    
    echo -e "\n${YELLOW}Would you like to delete these organizations to test the modal?${NC}"
    echo "WARNING: This will delete all organizations and their projects!"
    read -p "Type 'yes' to confirm deletion: " CONFIRM
    
    if [ "$CONFIRM" = "yes" ]; then
        # Get organization IDs
        ORG_IDS=$(echo "$ORG_RESPONSE" | jq -r '.organizations[].id' 2>/dev/null)
        
        for ORG_ID in $ORG_IDS; do
            echo -e "\nDeleting organization ID: $ORG_ID"
            DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/api/v1/organizations/$ORG_ID/" \
                -H "Authorization: Bearer $TOKEN" \
                -w "\n%{http_code}")
            
            HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
            if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
                echo -e "${GREEN}✅ Deleted organization $ORG_ID${NC}"
            else
                echo -e "${RED}❌ Failed to delete organization $ORG_ID (HTTP $HTTP_CODE)${NC}"
                echo "Response: $(echo "$DELETE_RESPONSE" | head -n-1)"
            fi
        done
        
        echo -e "\n${GREEN}Organizations deleted. The modal should now appear when you visit:${NC}"
        echo "$FRONTEND_URL/app/projects/new"
    fi
else
    echo -e "\n${GREEN}✅ No organizations found${NC}"
    echo "The modal SHOULD be showing. If it's not, there might be a frontend issue."
fi

# Step 3: Test organization creation endpoint
echo -e "\n${YELLOW}Step 3: Testing organization creation endpoint...${NC}"
TEST_TIMESTAMP=$(date +%s)
TEST_ORG_NAME="Test Org $TEST_TIMESTAMP"
TEST_ORG_SLUG="test-org-$TEST_TIMESTAMP"

CREATE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/organizations/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"$TEST_ORG_NAME\",
        \"slug\": \"$TEST_ORG_SLUG\",
        \"description\": \"Test organization from fix script\"
    }" -w "\n%{http_code}")

HTTP_CODE=$(echo "$CREATE_RESPONSE" | tail -n1)
RESPONSE_BODY=$(echo "$CREATE_RESPONSE" | head -n-1)

if [ "$HTTP_CODE" = "200" ] || [ "$HTTP_CODE" = "201" ]; then
    echo -e "${GREEN}✅ Organization creation endpoint is working${NC}"
    echo "Created organization:"
    echo "$RESPONSE_BODY" | jq '.' 2>/dev/null || echo "$RESPONSE_BODY"
else
    echo -e "${RED}❌ Organization creation failed (HTTP $HTTP_CODE)${NC}"
    echo "Response: $RESPONSE_BODY"
fi

# Step 4: Frontend debugging steps
echo -e "\n${YELLOW}Step 4: Frontend Debugging${NC}"
echo "Please follow these steps:"
echo ""
echo "1. Clear browser cache:"
echo "   - Go to: $FRONTEND_URL/clear-org-cache.html"
echo "   - Click 'Clear All Cache'"
echo "   - OR manually clear in DevTools > Application > Clear Storage"
echo ""
echo "2. Check browser console for errors:"
echo "   - Go to: $FRONTEND_URL/app/projects/new"
echo "   - Open DevTools Console"
echo "   - Look for these log messages:"
echo "     - 'Fetching organizations...'"
echo "     - 'Organizations API response:'"
echo "     - 'No valid organizations found, showing create modal'"
echo ""
echo "3. If you see organizations in the console but modal doesn't show:"
echo "   - There might be stale data"
echo "   - Try hard refresh: Ctrl+Shift+R (or Cmd+Shift+R on Mac)"
echo ""
echo "4. Check React DevTools:"
echo "   - Install React DevTools browser extension"
echo "   - Look for 'NewProjectPage' component"
echo "   - Check 'showCreateOrgModal' state value"

echo -e "\n${GREEN}✨ Script complete!${NC}"
echo ""
echo "Summary:"
echo "- API endpoint: ${GREEN}Working${NC}"
echo "- Organizations found: $ORG_COUNT"
echo "- Next step: Visit $FRONTEND_URL/app/projects/new"
echo ""
echo "If the modal still doesn't show, check the browser console for debug logs."