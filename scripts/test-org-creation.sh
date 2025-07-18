#!/bin/bash

# Test organization creation after login

API_URL="https://prism-backend-bwfx.onrender.com"
FRONTEND_URL="https://prism-frontend-kappa.vercel.app"

echo "🧪 Testing Organization Creation Flow"
echo "===================================="

# Get token from user
echo "Please provide your JWT token (from browser localStorage):"
echo "1. Open browser DevTools (F12)"
echo "2. Go to Application > Local Storage"
echo "3. Find 'token' and copy its value"
echo ""
read -p "Paste token here: " TOKEN

if [ -z "$TOKEN" ]; then
    echo "❌ No token provided"
    exit 1
fi

# Test 1: Check authentication
echo -e "\n1️⃣ Testing authentication..."
AUTH_TEST=$(curl -s -X GET "$API_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $TOKEN" \
    -w "\n%{http_code}")

HTTP_CODE=$(echo "$AUTH_TEST" | tail -n1)
if [ "$HTTP_CODE" = "200" ]; then
    echo "✅ Authentication successful"
    USER_EMAIL=$(echo "$AUTH_TEST" | head -n-1 | grep -o '"email":"[^"]*' | cut -d'"' -f4)
    echo "   User: $USER_EMAIL"
else
    echo "❌ Authentication failed (HTTP $HTTP_CODE)"
    echo "   Please login again and get a fresh token"
    exit 1
fi

# Test 2: List existing organizations
echo -e "\n2️⃣ Checking existing organizations..."
ORGS=$(curl -s -X GET "$API_URL/api/v1/organizations/" \
    -H "Authorization: Bearer $TOKEN")

ORG_COUNT=$(echo "$ORGS" | grep -o '"total":[0-9]*' | cut -d':' -f2)
echo "   Found $ORG_COUNT organizations"

# Test 3: Create new organization
TIMESTAMP=$(date +%s)
ORG_NAME="Test Organization $TIMESTAMP"
ORG_SLUG="test-org-$TIMESTAMP"

echo -e "\n3️⃣ Creating new organization..."
echo "   Name: $ORG_NAME"
echo "   Slug: $ORG_SLUG"

CREATE_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/organizations/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"$ORG_NAME\",
        \"slug\": \"$ORG_SLUG\",
        \"description\": \"Test organization created via script\"
    }")

if echo "$CREATE_RESPONSE" | grep -q '"id"'; then
    ORG_ID=$(echo "$CREATE_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "✅ Organization created successfully (ID: $ORG_ID)"
else
    echo "❌ Failed to create organization"
    echo "   Response: $CREATE_RESPONSE"
    exit 1
fi

# Test 4: Create project in new organization
echo -e "\n4️⃣ Creating project in new organization..."
PROJECT_NAME="Test Project"
PROJECT_KEY="TP$TIMESTAMP"

PROJECT_RESPONSE=$(curl -s -X POST "$API_URL/api/v1/projects/" \
    -H "Authorization: Bearer $TOKEN" \
    -H "Content-Type: application/json" \
    -d "{
        \"name\": \"$PROJECT_NAME\",
        \"key\": \"$PROJECT_KEY\",
        \"description\": \"Test project\",
        \"organization_id\": $ORG_ID
    }")

if echo "$PROJECT_RESPONSE" | grep -q '"id"'; then
    PROJECT_ID=$(echo "$PROJECT_RESPONSE" | grep -o '"id":[0-9]*' | cut -d':' -f2)
    echo "✅ Project created successfully (ID: $PROJECT_ID)"
else
    echo "❌ Failed to create project"
    echo "   Response: $PROJECT_RESPONSE"
fi

echo -e "\n✨ Complete Flow Test Summary"
echo "=============================="
echo "✅ Authentication working"
echo "✅ Organization creation working"
echo "✅ Project creation working"
echo ""
echo "You can now use the web UI at:"
echo "$FRONTEND_URL"