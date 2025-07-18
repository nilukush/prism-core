#!/bin/bash

echo "🔧 Force Delete Organization and Project"
echo "======================================"
echo ""

API_URL="https://prism-backend-bwfx.onrender.com"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${YELLOW}Step 1: Get your authentication token${NC}"
echo ""
echo "In your browser console at https://prism-frontend-kappa.vercel.app, run:"
echo -e "${GREEN}localStorage.getItem('token')${NC}"
echo ""
read -p "Paste your token here: " TOKEN

if [ -z "$TOKEN" ]; then
    echo -e "${RED}❌ No token provided${NC}"
    exit 1
fi

# Test authentication
echo -e "\n${YELLOW}Step 2: Testing authentication...${NC}"
AUTH_TEST=$(curl -s -X GET "$API_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $TOKEN" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$AUTH_TEST" | tail -n1)
if [ "$HTTP_CODE" != "200" ]; then
    echo -e "${RED}❌ Authentication failed (HTTP $HTTP_CODE)${NC}"
    echo "Token might be expired. Please login again."
    exit 1
fi

echo -e "${GREEN}✅ Authentication successful${NC}"

# Get organizations
echo -e "\n${YELLOW}Step 3: Fetching organizations...${NC}"
ORG_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/organizations/" \
    -H "Authorization: Bearer $TOKEN")

echo "Organizations found:"
echo "$ORG_RESPONSE" | jq '.'

# Extract organization ID
ORG_ID=$(echo "$ORG_RESPONSE" | jq -r '.organizations[0].id' 2>/dev/null)
ORG_NAME=$(echo "$ORG_RESPONSE" | jq -r '.organizations[0].name' 2>/dev/null)

if [ "$ORG_ID" != "null" ] && [ -n "$ORG_ID" ]; then
    echo -e "\n${YELLOW}Found organization: $ORG_NAME (ID: $ORG_ID)${NC}"
    
    # Try to delete via API first
    echo -e "\n${YELLOW}Step 4: Attempting to delete organization via API...${NC}"
    DELETE_RESPONSE=$(curl -s -X DELETE "$API_URL/api/v1/organizations/$ORG_ID/" \
        -H "Authorization: Bearer $TOKEN" \
        -w "\n%{http_code}")
    
    HTTP_CODE=$(echo "$DELETE_RESPONSE" | tail -n1)
    
    if [ "$HTTP_CODE" = "204" ] || [ "$HTTP_CODE" = "200" ]; then
        echo -e "${GREEN}✅ Organization deleted successfully!${NC}"
    elif [ "$HTTP_CODE" = "404" ]; then
        echo -e "${RED}❌ DELETE endpoint not found (404)${NC}"
        echo "The backend hasn't deployed the DELETE endpoint yet."
        echo ""
        echo -e "${YELLOW}Alternative: Database Deletion Required${NC}"
        echo "Since the DELETE endpoint isn't deployed yet, you need to:"
        echo ""
        echo "1. Go to Neon Dashboard: https://console.neon.tech"
        echo "2. Open SQL Editor for your database"
        echo "3. Run these queries:"
        echo ""
        echo -e "${GREEN}-- Delete all data in order${NC}"
        echo "DELETE FROM documents WHERE project_id IN (SELECT id FROM projects WHERE organization_id = $ORG_ID);"
        echo "DELETE FROM project_members WHERE project_id IN (SELECT id FROM projects WHERE organization_id = $ORG_ID);"
        echo "DELETE FROM projects WHERE organization_id = $ORG_ID;"
        echo "DELETE FROM organization_members WHERE organization_id = $ORG_ID;"
        echo "DELETE FROM organizations WHERE id = $ORG_ID;"
        echo ""
        echo "4. Then visit: https://prism-frontend-kappa.vercel.app/app/projects/new"
    else
        echo -e "${RED}❌ Failed to delete organization (HTTP $HTTP_CODE)${NC}"
        RESPONSE_BODY=$(echo "$DELETE_RESPONSE" | head -n-1)
        echo "Error: $RESPONSE_BODY"
    fi
else
    echo -e "${GREEN}✅ No organizations found!${NC}"
    echo "You should be able to create a new one."
fi

echo -e "\n${YELLOW}Step 5: Checking projects...${NC}"
PROJECTS_RESPONSE=$(curl -s -X GET "$API_URL/api/v1/projects/" \
    -H "Authorization: Bearer $TOKEN")

PROJECT_COUNT=$(echo "$PROJECTS_RESPONSE" | jq '.total' 2>/dev/null || echo "0")
echo "Projects found: $PROJECT_COUNT"

if [ "$PROJECT_COUNT" != "0" ] && [ "$PROJECT_COUNT" != "null" ]; then
    echo -e "${YELLOW}⚠️  Projects exist that may need deletion${NC}"
    echo "$PROJECTS_RESPONSE" | jq '.projects[] | {id, name, organization_id}'
fi

echo -e "\n${GREEN}✨ Next Steps:${NC}"
echo "1. If organization was deleted, clear browser cache:"
echo "   - Visit: https://prism-frontend-kappa.vercel.app/clear-org-cache.html"
echo "2. Then visit: https://prism-frontend-kappa.vercel.app/app/projects/new"
echo "3. The organization creation modal should appear"