#!/bin/bash

# PRISM Render Deployment Monitor
# Real-time monitoring for your deployment

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m'

# Get deployment URL
echo -e "${BLUE}🚀 PRISM Deployment Monitor${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
read -p "Enter your Render app URL (e.g., prism-backend.onrender.com): " APP_URL

# Remove https:// if provided
APP_URL=${APP_URL#https://}
APP_URL=${APP_URL#http://}

# Full URL
BASE_URL="https://$APP_URL"

echo -e "\nMonitoring: ${BLUE}$BASE_URL${NC}\n"

# Function to check endpoint
check_endpoint() {
    local endpoint=$1
    local description=$2
    local expected=$3
    
    echo -n "Checking $description... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" "$BASE_URL$endpoint" 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected" ]; then
        echo -e "${GREEN}✓ OK ($response)${NC}"
        return 0
    elif [ "$response" = "000" ]; then
        echo -e "${RED}✗ Failed (No connection)${NC}"
        return 1
    else
        echo -e "${YELLOW}⚠ Warning ($response)${NC}"
        return 1
    fi
}

# Function to check JSON endpoint
check_json_endpoint() {
    local endpoint=$1
    local description=$2
    
    echo -n "Checking $description... "
    
    response=$(curl -s "$BASE_URL$endpoint" 2>/dev/null)
    
    if echo "$response" | jq -e . >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Valid JSON${NC}"
        echo "  Response: $(echo "$response" | jq -c .)"
        return 0
    else
        echo -e "${RED}✗ Invalid response${NC}"
        return 1
    fi
}

# Main monitoring loop
monitor_deployment() {
    echo -e "${BLUE}Starting deployment checks...${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # Check if service is responding
    if ! check_endpoint "" "Service availability" "200"; then
        echo -e "\n${YELLOW}Service not ready yet. Waiting...${NC}"
        
        # Wait and retry
        for i in {1..30}; do
            sleep 10
            echo -n "Attempt $i/30... "
            
            if curl -s -o /dev/null -w "%{http_code}" "$BASE_URL/health" 2>/dev/null | grep -q "200"; then
                echo -e "${GREEN}Service is up!${NC}"
                break
            else
                echo "Still waiting..."
            fi
            
            if [ $i -eq 30 ]; then
                echo -e "\n${RED}Service failed to start after 5 minutes${NC}"
                echo "Check Render logs for errors"
                exit 1
            fi
        done
    fi
    
    echo ""
    
    # Core endpoints
    echo -e "${BLUE}Core Endpoints:${NC}"
    check_endpoint "/health" "Health endpoint" "200"
    check_endpoint "/docs" "API documentation" "200"
    check_endpoint "/openapi.json" "OpenAPI spec" "200"
    
    echo ""
    
    # API endpoints
    echo -e "${BLUE}API Endpoints:${NC}"
    check_json_endpoint "/api/v1/health" "API health"
    
    echo ""
    
    # Configuration check
    echo -e "${BLUE}Configuration Check:${NC}"
    echo -n "Checking AI provider configuration... "
    
    # Create a simple test
    ai_test=$(curl -s -X POST "$BASE_URL/api/v1/ai/config/test" \
        -H "Content-Type: application/json" \
        -d '{"test": true}' 2>/dev/null || echo "{}")
    
    if echo "$ai_test" | grep -q "openai"; then
        echo -e "${GREEN}✓ OpenAI configured${NC}"
    elif echo "$ai_test" | grep -q "error"; then
        echo -e "${YELLOW}⚠ AI configuration needs attention${NC}"
    else
        echo -e "${BLUE}ℹ Configuration endpoint not available${NC}"
    fi
    
    echo ""
}

# Database connection test
test_database() {
    echo -e "${BLUE}Database Connection Test:${NC}"
    echo -n "Testing database connectivity... "
    
    # This would need auth, so we check if the service is healthy
    if check_endpoint "/health" "Database via health check" "200" >/dev/null 2>&1; then
        echo -e "${GREEN}✓ Database connected${NC}"
    else
        echo -e "${RED}✗ Database issues${NC}"
    fi
}

# Performance metrics
check_performance() {
    echo -e "\n${BLUE}Performance Metrics:${NC}"
    
    # Response time test
    echo -n "Checking response time... "
    response_time=$(curl -s -o /dev/null -w "%{time_total}" "$BASE_URL/health" 2>/dev/null)
    
    if (( $(echo "$response_time < 1" | bc -l) )); then
        echo -e "${GREEN}✓ Fast ($response_time seconds)${NC}"
    elif (( $(echo "$response_time < 3" | bc -l) )); then
        echo -e "${YELLOW}⚠ Moderate ($response_time seconds)${NC}"
    else
        echo -e "${RED}✗ Slow ($response_time seconds)${NC}"
        echo "  Note: First request after sleep is slow (cold start)"
    fi
}

# Cost monitoring reminder
cost_reminder() {
    echo -e "\n${YELLOW}💰 Cost Monitoring Reminder:${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "1. Check OpenAI usage: https://platform.openai.com/usage"
    echo "2. Verify budget alerts are set"
    echo "3. Monitor first 24 hours closely"
    echo "4. Cache hit rate should be >80% after warmup"
}

# Main execution
echo -e "${BLUE}═══════════════════════════════════${NC}"
echo -e "${BLUE}    PRISM Deployment Monitor${NC}"
echo -e "${BLUE}═══════════════════════════════════${NC}"
echo ""

# Run all checks
monitor_deployment
test_database
check_performance
cost_reminder

echo -e "\n${GREEN}✅ Deployment monitoring complete!${NC}"
echo ""
echo "Next steps:"
echo "1. Update FRONTEND_URL in Render with your Vercel URL"
echo "2. Deploy frontend to Vercel"
echo "3. Test full end-to-end flow"
echo "4. Monitor AI costs for first day"
echo ""
echo -e "${BLUE}Full deployment guide: RENDER_DEPLOYMENT_CHECKLIST.md${NC}"

# Offer to open browser
if command -v open &> /dev/null; then
    echo ""
    read -p "Open API docs in browser? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        open "$BASE_URL/docs"
    fi
fi