#!/bin/bash

# PRISM Activation Status Monitor
# This script monitors the current state of user activation in production

set -e

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

BACKEND_URL="https://prism-backend-bwfx.onrender.com"

echo -e "${BLUE}📊 PRISM User Activation Status Monitor${NC}"
echo "================================================"
echo "Backend: $BACKEND_URL"
echo "Time: $(date)"
echo "================================================"

# Function to test activation endpoint
test_activation() {
    local email=$1
    echo -e "\n${YELLOW}Testing activation for: $email${NC}"
    
    # Test activation endpoint
    response=$(curl -s -X POST "$BACKEND_URL/api/v1/activation/simple/$email" 2>&1)
    
    if echo "$response" | grep -q "activated successfully"; then
        echo -e "${GREEN}✅ Activation endpoint working - User activated${NC}"
    elif echo "$response" | grep -q "User not found"; then
        echo -e "${YELLOW}⚠️  User not found (expected for non-existent users)${NC}"
    elif echo "$response" | grep -q "already active"; then
        echo -e "${GREEN}✅ User already active${NC}"
    else
        echo -e "${RED}❌ Unexpected response: $response${NC}"
    fi
}

# Check backend health
echo -e "\n${YELLOW}1. Backend Health Check${NC}"
if curl -s -f -o /dev/null "$BACKEND_URL/health"; then
    echo -e "${GREEN}✅ Backend is healthy${NC}"
else
    echo -e "${RED}❌ Backend is down or unreachable${NC}"
    exit 1
fi

# Test activation endpoint with various scenarios
echo -e "\n${YELLOW}2. Activation Endpoint Tests${NC}"

# Test with your email
test_activation "nilukush@gmail.com"

# Test with non-existent email
test_activation "nonexistent-$(date +%s)@example.com"

# SQL queries to run in Neon
echo -e "\n${YELLOW}3. Database Queries to Run in Neon${NC}"
echo "Copy and run these queries in your Neon SQL editor:"
echo ""
echo -e "${BLUE}-- Overall user statistics${NC}"
cat << 'EOF'
SELECT 
    status,
    COUNT(*) as count,
    ROUND(100.0 * COUNT(*) / SUM(COUNT(*)) OVER(), 2) as percentage
FROM users 
GROUP BY status
ORDER BY count DESC;
EOF

echo ""
echo -e "${BLUE}-- Recent registrations (last 24 hours)${NC}"
cat << 'EOF'
SELECT 
    email,
    status,
    email_verified,
    created_at,
    email_verified_at
FROM users 
WHERE created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC
LIMIT 10;
EOF

echo ""
echo -e "${BLUE}-- Pending users that need activation${NC}"
cat << 'EOF'
SELECT 
    email,
    created_at,
    EXTRACT(EPOCH FROM (NOW() - created_at))/3600 as hours_since_registration
FROM users 
WHERE status = 'pending'
ORDER BY created_at DESC
LIMIT 20;
EOF

echo ""
echo -e "${BLUE}-- Activation success rate (last 7 days)${NC}"
cat << 'EOF'
SELECT 
    DATE(created_at) as registration_date,
    COUNT(*) as total_users,
    SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) as active_users,
    ROUND(100.0 * SUM(CASE WHEN status = 'active' THEN 1 ELSE 0 END) / COUNT(*), 2) as activation_rate
FROM users 
WHERE created_at > NOW() - INTERVAL '7 days'
GROUP BY DATE(created_at)
ORDER BY registration_date DESC;
EOF

# Provide activation command examples
echo -e "\n${YELLOW}4. Quick Activation Commands${NC}"
echo "To activate a specific user:"
echo -e "${BLUE}curl -X POST $BACKEND_URL/api/v1/activation/simple/user@example.com${NC}"
echo ""
echo "To activate multiple users, create a file 'emails.txt' with one email per line, then run:"
echo -e "${BLUE}while IFS= read -r email; do curl -X POST $BACKEND_URL/api/v1/activation/simple/\$email; done < emails.txt${NC}"

# Summary
echo -e "\n${GREEN}================================================${NC}"
echo -e "${GREEN}Monitoring complete!${NC}"
echo -e "${GREEN}================================================${NC}"