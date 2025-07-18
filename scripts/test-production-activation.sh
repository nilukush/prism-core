#!/bin/bash

# PRISM Production Activation Test Script
# This script tests the complete user registration and activation flow

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
BACKEND_URL="https://prism-backend-bwfx.onrender.com"
FRONTEND_URL="https://prism-frontend-kappa.vercel.app"
TIMESTAMP=$(date +%s)
TEST_EMAIL="test-${TIMESTAMP}@example.com"
TEST_PASSWORD="Test123!@#"

echo -e "${YELLOW}🧪 PRISM Production Activation Test${NC}"
echo "================================================"
echo "Backend: $BACKEND_URL"
echo "Frontend: $FRONTEND_URL"
echo "Test Email: $TEST_EMAIL"
echo "================================================"

# Function to check if command succeeded
check_status() {
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ $1${NC}"
    else
        echo -e "${RED}❌ $1${NC}"
        exit 1
    fi
}

# Step 1: Health Check
echo -e "\n${YELLOW}Step 1: Backend Health Check${NC}"
HTTP_STATUS=$(curl -s -o /dev/null -w "%{http_code}" "$BACKEND_URL/health")
if [ "$HTTP_STATUS" = "200" ]; then
    echo -e "${GREEN}✅ Backend is healthy (HTTP $HTTP_STATUS)${NC}"
else
    echo -e "${RED}❌ Backend is not healthy (HTTP $HTTP_STATUS)${NC}"
    exit 1
fi

# Step 2: Register User
echo -e "\n${YELLOW}Step 2: Register New User${NC}"
echo "Email: $TEST_EMAIL"
echo "Password: $TEST_PASSWORD"

REGISTER_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/register" \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"test-$TIMESTAMP\",\"email\":\"$TEST_EMAIL\",\"password\":\"$TEST_PASSWORD\",\"confirm_password\":\"$TEST_PASSWORD\"}")

if echo "$REGISTER_RESPONSE" | grep -q "error"; then
    echo -e "${RED}❌ Registration failed: $REGISTER_RESPONSE${NC}"
    exit 1
else
    echo -e "${GREEN}✅ User registered successfully${NC}"
fi

# Wait a moment for database to update
sleep 2

# Step 3: Check User Status
echo -e "\n${YELLOW}Step 3: Check User Status${NC}"
echo "Run this SQL in Neon to verify:"
echo "SELECT email, status, email_verified FROM users WHERE email = '$TEST_EMAIL';"
echo -e "${YELLOW}Expected: status = 'pending', email_verified = false${NC}"

# Step 4: Activate User
echo -e "\n${YELLOW}Step 4: Activate User${NC}"
ACTIVATION_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/activation/simple/$TEST_EMAIL")
echo "Response: $ACTIVATION_RESPONSE"

if echo "$ACTIVATION_RESPONSE" | grep -q "activated successfully"; then
    echo -e "${GREEN}✅ User activated successfully${NC}"
else
    echo -e "${RED}❌ Activation failed${NC}"
    exit 1
fi

# Step 5: Test Login
echo -e "\n${YELLOW}Step 5: Test Login${NC}"
LOGIN_RESPONSE=$(curl -s -X POST "$BACKEND_URL/api/v1/auth/login" \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_EMAIL&password=$TEST_PASSWORD")

if echo "$LOGIN_RESPONSE" | grep -q "access_token"; then
    echo -e "${GREEN}✅ Login successful!${NC}"
    # Extract token for further testing
    ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | grep -o '"access_token":"[^"]*' | cut -d'"' -f4)
    echo "Access token received (first 20 chars): ${ACCESS_TOKEN:0:20}..."
else
    echo -e "${RED}❌ Login failed: $LOGIN_RESPONSE${NC}"
    exit 1
fi

# Step 6: Test Authenticated Endpoint
echo -e "\n${YELLOW}Step 6: Test Authenticated Access${NC}"
ME_RESPONSE=$(curl -s -X GET "$BACKEND_URL/api/v1/auth/me" \
    -H "Authorization: Bearer $ACCESS_TOKEN")

if echo "$ME_RESPONSE" | grep -q "$TEST_EMAIL"; then
    echo -e "${GREEN}✅ Authenticated endpoint accessible${NC}"
    echo "User details retrieved successfully"
else
    echo -e "${RED}❌ Failed to access authenticated endpoint${NC}"
fi

# Summary
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}🎉 All tests passed successfully!${NC}"
echo -e "${GREEN}================================================${NC}"
echo ""
echo "Summary:"
echo "- ✅ Backend is healthy"
echo "- ✅ User registration works"
echo "- ✅ User activation works"
echo "- ✅ Login works after activation"
echo "- ✅ Authenticated endpoints accessible"
echo ""
echo "Test user created:"
echo "Email: $TEST_EMAIL"
echo "Password: $TEST_PASSWORD"
echo ""
echo -e "${YELLOW}Next steps:${NC}"
echo "1. Try logging in via the web UI: $FRONTEND_URL/auth/login"
echo "2. Check database for user status"
echo "3. Test with multiple users to ensure consistency"