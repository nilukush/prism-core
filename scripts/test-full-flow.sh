#!/bin/bash

# Configuration
API_URL="https://prism-backend-bwfx.onrender.com"
TIMESTAMP=$(date +%s)
TEST_USER="testuser$TIMESTAMP"
TEST_EMAIL="test$TIMESTAMP@example.com"
TEST_PASS="Test123456@"

echo "🚀 Testing PRISM Full User Flow"
echo "================================"

# 1. Register
echo -e "\n1️⃣  Registering user: $TEST_EMAIL"
REGISTER=$(curl -s -X POST "$API_URL/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d "{
    \"username\": \"$TEST_USER\",
    \"email\": \"$TEST_EMAIL\",
    \"password\": \"$TEST_PASS\",
    \"confirm_password\": \"$TEST_PASS\"
  }")

if echo "$REGISTER" | grep -q "id"; then
  echo "✅ Registration successful"
else
  echo "❌ Registration failed: $REGISTER"
  exit 1
fi

# 2. Login
echo -e "\n2️⃣  Logging in..."
LOGIN=$(curl -s -X POST "$API_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=$TEST_EMAIL&password=$TEST_PASS")

TOKEN=$(echo "$LOGIN" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
if [ -n "$TOKEN" ]; then
  echo "✅ Login successful"
else
  echo "❌ Login failed: $LOGIN"
  exit 1
fi

# 3. Create Organization
echo -e "\n3️⃣  Creating organization..."
ORG=$(curl -s -X POST "$API_URL/api/v1/organizations/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Org $TIMESTAMP\",
    \"slug\": \"test-org-$TIMESTAMP\",
    \"description\": \"Test organization\"
  }")

ORG_ID=$(echo "$ORG" | grep -o '"id":[0-9]*' | cut -d':' -f2)
if [ -n "$ORG_ID" ]; then
  echo "✅ Organization created (ID: $ORG_ID)"
else
  echo "❌ Organization creation failed: $ORG"
  exit 1
fi

# 4. Create Project
echo -e "\n4️⃣  Creating project..."
PROJECT=$(curl -s -X POST "$API_URL/api/v1/projects/" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d "{
    \"name\": \"Test Project\",
    \"key\": \"TP$TIMESTAMP\",
    \"description\": \"Test project\",
    \"organization_id\": $ORG_ID
  }")

if echo "$PROJECT" | grep -q "id"; then
  echo "✅ Project created successfully"
else
  echo "❌ Project creation failed: $PROJECT"
  exit 1
fi

echo -e "\n🎉 Full flow completed successfully!"
echo "User: $TEST_EMAIL"
echo "Organization ID: $ORG_ID"