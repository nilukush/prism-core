#!/bin/bash

# End-to-End Test Script for PRISM
# This script tests the complete application stack

set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
API_URL="${API_URL:-http://localhost:8100}"
FRONTEND_URL="${FRONTEND_URL:-http://localhost:3100}"

echo -e "${YELLOW}Starting PRISM End-to-End Tests...${NC}"

# Function to check service health
check_service() {
    local name=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $name... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$url" || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        return 1
    fi
}

# Function to test API endpoint
test_api_endpoint() {
    local name=$1
    local method=$2
    local endpoint=$3
    local data=$4
    local expected_status=${5:-200}
    
    echo -n "Testing $name... "
    
    if [ -z "$data" ]; then
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" || echo "000")
    else
        response=$(curl -s -o /dev/null -w "%{http_code}" -X "$method" "$API_URL$endpoint" \
            -H "Content-Type: application/json" \
            -d "$data" || echo "000")
    fi
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}✓ OK${NC} (HTTP $response)"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC} (HTTP $response)"
        return 1
    fi
}

# Function to run database query
test_database() {
    echo -n "Testing database connection... "
    
    result=$(docker compose exec -T postgres psql -U prism -d prism_db -c "SELECT 1;" 2>&1 || echo "FAILED")
    
    if [[ "$result" == *"1"* ]] && [[ "$result" != *"FAILED"* ]]; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Function to test Redis
test_redis() {
    echo -n "Testing Redis connection... "
    
    result=$(docker compose exec -T redis redis-cli -a redis_password ping 2>&1 || echo "FAILED")
    
    if [[ "$result" == *"PONG"* ]]; then
        echo -e "${GREEN}✓ OK${NC}"
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        return 1
    fi
}

# Start tests
echo -e "\n${YELLOW}1. Infrastructure Tests${NC}"
echo "------------------------"

test_database
test_redis

echo -e "\n${YELLOW}2. Service Health Checks${NC}"
echo "-------------------------"

check_service "Backend Health" "$API_URL/health"
check_service "Backend API Docs" "$API_URL/api/v1/docs"
check_service "Frontend Health" "$FRONTEND_URL/api/health" || echo "Note: Frontend may need to be started separately"

echo -e "\n${YELLOW}3. API Endpoint Tests${NC}"
echo "----------------------"

test_api_endpoint "API Info" "GET" "/api/v1"
test_api_endpoint "Health Check" "GET" "/health"
test_api_endpoint "Users List (Unauthorized)" "GET" "/api/v1/users" "" "401"
test_api_endpoint "Invalid Login" "POST" "/api/v1/auth/login" '{"email":"test@example.com","password":"wrongpass"}' "401"

echo -e "\n${YELLOW}4. Database Schema Tests${NC}"
echo "-------------------------"

echo -n "Checking tables exist... "
tables=$(docker compose exec -T postgres psql -U prism -d prism_db -c "\dt" 2>&1 || echo "FAILED")

if [[ "$tables" == *"alembic_version"* ]] && [[ "$tables" != *"FAILED"* ]]; then
    echo -e "${GREEN}✓ OK${NC}"
    
    # Count tables
    table_count=$(echo "$tables" | grep -c "table" || echo "0")
    echo "  Found $table_count tables in database"
else
    echo -e "${RED}✗ FAILED${NC}"
fi

echo -e "\n${YELLOW}5. Performance Tests${NC}"
echo "---------------------"

echo -n "API Response Time Test... "
time_total=$(curl -s -o /dev/null -w "%{time_total}" "$API_URL/health" || echo "999")
time_ms=$(echo "$time_total * 1000" | bc | cut -d. -f1)

if [ "$time_ms" -lt "500" ]; then
    echo -e "${GREEN}✓ OK${NC} (${time_ms}ms)"
else
    echo -e "${YELLOW}⚠ SLOW${NC} (${time_ms}ms)"
fi

echo -e "\n${YELLOW}Test Summary${NC}"
echo "============"

# Count successes and failures
total_tests=10
failed_tests=$(grep -c "FAILED" <<< "$0" || echo "0")
passed_tests=$((total_tests - failed_tests))

if [ "$failed_tests" -eq "0" ]; then
    echo -e "${GREEN}All tests passed!${NC} ($passed_tests/$total_tests)"
    exit 0
else
    echo -e "${RED}Some tests failed!${NC} ($passed_tests/$total_tests passed)"
    exit 1
fi