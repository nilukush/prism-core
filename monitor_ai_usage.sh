#!/bin/bash

# Monitor AI API Usage in Real-time
# This script helps identify unexpected API calls and usage patterns

echo "🔍 AI API Usage Monitor"
echo "======================="
echo

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to show usage summary
show_summary() {
    echo -e "${BLUE}📊 AI Usage Summary (Last Hour)${NC}"
    echo "--------------------------------"
    
    # Count total requests
    TOTAL_REQUESTS=$(docker compose logs backend --since 1h 2>/dev/null | grep -c "anthropic_request")
    echo -e "Total Anthropic Requests: ${YELLOW}$TOTAL_REQUESTS${NC}"
    
    # Count errors
    TOTAL_ERRORS=$(docker compose logs backend --since 1h 2>/dev/null | grep -c "anthropic_generation_error")
    echo -e "Failed Requests: ${RED}$TOTAL_ERRORS${NC}"
    
    # Count timeouts
    TIMEOUTS=$(docker compose logs backend --since 1h 2>/dev/null | grep -c "ReadTimeout")
    echo -e "Timeout Errors: ${RED}$TIMEOUTS${NC}"
    
    # Unique users
    UNIQUE_USERS=$(docker compose logs backend --since 1h 2>/dev/null | grep "prd_generation_request" | grep -oP 'user_id":\s*\K\d+' | sort -u | wc -l)
    echo -e "Unique Users: ${GREEN}$UNIQUE_USERS${NC}"
    
    echo
}

# Function to show recent requests
show_recent_requests() {
    echo -e "${BLUE}🕐 Recent AI Requests (Last 10)${NC}"
    echo "--------------------------------"
    docker compose logs backend --tail 1000 2>/dev/null | grep "anthropic_request" | tail -10 | while read -r line; do
        # Extract key information
        TIMESTAMP=$(echo "$line" | grep -oP 'timestamp":\s*"\K[^"]+' | cut -d'T' -f2 | cut -d'.' -f1)
        MODEL=$(echo "$line" | grep -oP 'model":\s*"\K[^"]+')
        TOKENS=$(echo "$line" | grep -oP 'max_tokens":\s*\K\d+')
        
        echo -e "${TIMESTAMP} - Model: ${GREEN}$MODEL${NC}, Max Tokens: ${YELLOW}$TOKENS${NC}"
    done
    echo
}

# Function to check for suspicious patterns
check_suspicious_patterns() {
    echo -e "${BLUE}🚨 Checking for Suspicious Patterns${NC}"
    echo "------------------------------------"
    
    # Check for rapid repeated requests (more than 3 in 1 minute from same user)
    RAPID_REQUESTS=$(docker compose logs backend --since 10m 2>/dev/null | grep "prd_generation_request" | \
        grep -oP 'user_id":\s*\K\d+|timestamp":\s*"\K[^"]+' | \
        awk 'NR%2{printf "%s ",$0;next;}1' | \
        awk '{print $1, substr($2,12,8)}' | \
        sort | uniq -c | \
        awk '$1 > 3 {print "User", $2, "made", $1, "requests in short time"}')
    
    if [ -n "$RAPID_REQUESTS" ]; then
        echo -e "${RED}⚠️  Rapid repeated requests detected:${NC}"
        echo "$RAPID_REQUESTS"
    else
        echo -e "${GREEN}✅ No rapid repeated requests detected${NC}"
    fi
    
    # Check for requests during off-hours (customize based on your timezone)
    CURRENT_HOUR=$(date +%H)
    if [ "$CURRENT_HOUR" -lt 6 ] || [ "$CURRENT_HOUR" -gt 22 ]; then
        OFF_HOUR_REQUESTS=$(docker compose logs backend --since 1h 2>/dev/null | grep -c "anthropic_request")
        if [ "$OFF_HOUR_REQUESTS" -gt 0 ]; then
            echo -e "${YELLOW}⚠️  Off-hours API usage detected: $OFF_HOUR_REQUESTS requests${NC}"
        fi
    fi
    
    echo
}

# Function to estimate costs
estimate_costs() {
    echo -e "${BLUE}💰 Estimated API Costs${NC}"
    echo "----------------------"
    
    # Get token usage from recent requests
    TOTAL_TOKENS=$(docker compose logs backend --since 24h 2>/dev/null | \
        grep "anthropic_generation_complete" | \
        grep -oP 'tokens":\s*\K\d+' | \
        awk '{sum += $1} END {print sum}')
    
    if [ -z "$TOTAL_TOKENS" ]; then
        TOTAL_TOKENS=0
    fi
    
    # Claude 3 Sonnet pricing (approximate)
    # $3 per 1M input tokens, $15 per 1M output tokens
    # Assuming 70% input, 30% output ratio
    INPUT_TOKENS=$((TOTAL_TOKENS * 70 / 100))
    OUTPUT_TOKENS=$((TOTAL_TOKENS * 30 / 100))
    
    INPUT_COST=$(echo "scale=4; $INPUT_TOKENS * 0.000003" | bc)
    OUTPUT_COST=$(echo "scale=4; $OUTPUT_TOKENS * 0.000015" | bc)
    TOTAL_COST=$(echo "scale=2; $INPUT_COST + $OUTPUT_COST" | bc)
    
    echo -e "Total Tokens (24h): ${YELLOW}$TOTAL_TOKENS${NC}"
    echo -e "Estimated Cost (24h): ${GREEN}\$$TOTAL_COST${NC}"
    echo
}

# Function to monitor in real-time
monitor_realtime() {
    echo -e "${BLUE}📡 Real-time Monitoring (Press Ctrl+C to stop)${NC}"
    echo "----------------------------------------------"
    echo
    
    # Monitor logs in real-time, highlighting AI requests
    docker compose logs -f backend 2>/dev/null | grep --line-buffered -E "anthropic_request|prd_generation_request|anthropic_generation_error" | while read -r line; do
        if echo "$line" | grep -q "error"; then
            echo -e "${RED}❌ ERROR: $line${NC}"
        elif echo "$line" | grep -q "anthropic_request"; then
            TIMESTAMP=$(echo "$line" | grep -oP 'timestamp":\s*"\K[^"]+' | cut -d'T' -f2 | cut -d'.' -f1)
            echo -e "${GREEN}🤖 API Call at $TIMESTAMP${NC}"
        else
            echo -e "${YELLOW}📝 $line${NC}"
        fi
    done
}

# Main menu
while true; do
    echo -e "${BLUE}Select an option:${NC}"
    echo "1) Show usage summary"
    echo "2) Show recent requests"
    echo "3) Check suspicious patterns"
    echo "4) Estimate costs"
    echo "5) Monitor real-time"
    echo "6) Export detailed log"
    echo "q) Quit"
    echo
    read -p "Option: " choice
    
    case $choice in
        1)
            show_summary
            ;;
        2)
            show_recent_requests
            ;;
        3)
            check_suspicious_patterns
            ;;
        4)
            estimate_costs
            ;;
        5)
            monitor_realtime
            ;;
        6)
            TIMESTAMP=$(date +%Y%m%d_%H%M%S)
            LOGFILE="ai_usage_log_$TIMESTAMP.txt"
            echo "Exporting detailed log to $LOGFILE..."
            docker compose logs backend --since 24h 2>/dev/null | grep -E "anthropic|ai_" > "$LOGFILE"
            echo -e "${GREEN}✅ Log exported to $LOGFILE${NC}"
            echo
            ;;
        q|Q)
            echo "Exiting monitor..."
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid option${NC}"
            echo
            ;;
    esac
done