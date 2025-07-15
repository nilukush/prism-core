#!/bin/bash
# Test script for PRISM Project API endpoints

BASE_URL="http://localhost:8000/api/v1"
EMAIL="test@example.com"  # Update with your test user
PASSWORD="password123"    # Update with your test password

echo "🚀 Testing PRISM Project API"
echo "================================"

# Step 1: Login
echo -e "\n1️⃣ Logging in..."
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$EMAIL&password=$PASSWORD")

TOKEN=$(echo $LOGIN_RESPONSE | jq -r '.access_token')

if [ "$TOKEN" == "null" ] || [ -z "$TOKEN" ]; then
  echo "❌ Login failed!"
  echo "Response: $LOGIN_RESPONSE"
  exit 1
fi

echo "✅ Login successful! Token obtained."

# Step 2: List organizations
echo -e "\n2️⃣ Listing organizations..."
ORGS_RESPONSE=$(curl -s -X GET "$BASE_URL/organizations" \
  -H "Authorization: Bearer $TOKEN")

echo "Organizations: $ORGS_RESPONSE" | jq '.'

# Get first organization ID
ORG_ID=$(echo $ORGS_RESPONSE | jq -r '.[0].id')

if [ "$ORG_ID" == "null" ] || [ -z "$ORG_ID" ]; then
  echo "❌ No organizations found!"
  exit 1
fi

echo "✅ Using organization ID: $ORG_ID"

# Step 3: Create a project
echo -e "\n3️⃣ Creating a new project..."
TIMESTAMP=$(date +%s)
PROJECT_KEY="TST${TIMESTAMP: -3}"

PROJECT_DATA=$(cat <<EOF
{
  "name": "Test Project $TIMESTAMP",
  "key": "$PROJECT_KEY",
  "description": "Created via API test script",
  "status": "planning",
  "organization_id": $ORG_ID
}
EOF
)

echo "Project data: $PROJECT_DATA" | jq '.'

CREATE_RESPONSE=$(curl -s -X POST "$BASE_URL/projects" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "$PROJECT_DATA")

echo "Create response: $CREATE_RESPONSE" | jq '.'

PROJECT_ID=$(echo $CREATE_RESPONSE | jq -r '.id')

if [ "$PROJECT_ID" == "null" ] || [ -z "$PROJECT_ID" ]; then
  echo "❌ Project creation failed!"
else
  echo "✅ Project created with ID: $PROJECT_ID"
fi

# Step 4: List all projects
echo -e "\n4️⃣ Listing all projects..."
PROJECTS_RESPONSE=$(curl -s -X GET "$BASE_URL/projects" \
  -H "Authorization: Bearer $TOKEN")

echo "Projects: $PROJECTS_RESPONSE" | jq '.'

echo -e "\n✅ Test completed!"